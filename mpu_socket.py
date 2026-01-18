#!/usr/bin/env python3
from __future__ import annotations
import sys , signal
import socket
import selectors
import json
import logging
import queue
import threading
from typing import Any, TypeAlias

from mpu_buffer import MPU9250Buffer, MPUChannel, SensorData

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

ClientState: TypeAlias = dict[str, Any]

class MPUSocketServerNonBlocking:
    _mpu: MPU9250Buffer
    _selector: selectors.DefaultSelector
    _clients: dict[socket.socket, ClientState]
    _is_running: bool
    _clients_lock: threading.RLock

    def __init__(self, mpu_buffer: MPU9250Buffer, host: str = '0.0.0.0', port: int = 8888) -> None:
        self._mpu = mpu_buffer
        self._selector = selectors.DefaultSelector()
        self._clients = {}
        self._clients_lock = threading.RLock()
        self._is_running = False
        
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setblocking(False)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((host, port))
        self._server_sock.listen(3)
        
        self._selector.register(self._server_sock, selectors.EVENT_READ, self._accept)

    def _accept(self, sock: socket.socket, mask: int) -> None:
        try:
            conn, addr = sock.accept()
            if len(self._clients) >= 3:
                logging.warning(f"拒絕連線 {addr}：已達上限")
                conn.close()
                return
                
            logging.info(f"新連線來自：{addr}")
            conn.setblocking(False)
            
            with self._clients_lock:
                self._clients[conn] = {
                    "mask": MPUChannel.NONE,
                    "streaming": False,
                    "buffer": ""
                }
            
            self._selector.register(conn, selectors.EVENT_READ, self._read_command)
        except BlockingIOError:
            pass

    def _read_command(self, conn: socket.socket, mask: int) -> None:
        """針對 Windows ConnectionResetError 進行優化處理"""
        try:
            # 在 Windows 下，Client 斷開可能會在這裡直接拋出例外
            data = conn.recv(1024).decode('utf-8')
            
            # Linux 下正常的斷開會回傳空資料
            if not data:
                self._remove_client(conn)
                return
                
            with self._clients_lock:
                state = self._clients[conn]
                state["buffer"] += data
                
                while "\n" in state["buffer"]:
                    line, state["buffer"] = state["buffer"].split("\n", 1)
                    try:
                        cmd = json.loads(line)
                        self._process_command(conn, cmd)
                    except json.JSONDecodeError:
                        pass
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            # 捕獲所有 Windows 常見的斷開例外，執行清理
            logging.info("偵測到 Client 端強制中斷連線 (Windows Reset)")
            self._remove_client(conn)
        except Exception as e:
            logging.error(f"讀取指令發生未知錯誤: {e}")
            self._remove_client(conn)

    def _process_command(self, conn: socket.socket, cmd: dict[str, Any]) -> None:
        action = cmd.get("action")
        params = cmd.get("params", [])
        
        with self._clients_lock:
            if action == "config_channels":
                new_mask = MPUChannel.NONE
                for p in params:
                    try: new_mask |= MPUChannel[p.upper()]
                    except: pass
                self._clients[conn]["mask"] = new_mask
                # 配置變更後立即更新硬體
                self._update_hardware()
                
            elif action == "start_send":
                self._clients[conn]["streaming"] = True
                self._update_hardware()
                
            elif action == "stop_send":
                self._clients[conn]["streaming"] = False
                self._update_hardware()
                
            elif action == "disconnect":
                self._remove_client(conn)

    def _update_hardware(self) -> None:
        """解決無 Client 卻持續 Run 以及 Channel 配置切換問題"""
        with self._clients_lock:
            union_mask = MPUChannel.NONE
            any_streaming = False
            
            # 重新計算所有 Client 的需求
            for info in self._clients.values():
                union_mask |= info["mask"]
                if info["streaming"]:
                    any_streaming = True
            
            # 1. 如果有需求，更新硬體配置 (config_channels 會重新計算 packet_size)
            if union_mask != MPUChannel.NONE:
                self._mpu.config_channels(union_mask)
                self._flush_queue() # 切換配置後清空過期資料
            
            # 2. 自動管理執行緒啟動與停止
            if any_streaming:
                if not self._mpu._running:
                    logging.info("偵測到串流需求，開啟 MPU 讀取執行緒")
                    self._mpu.start()
            else:
                if self._mpu._running:
                    logging.info("目前無活動串流，停止 MPU 讀取執行緒以節省資源")
                    self._mpu.stop()

    def _flush_queue(self) -> None:
        q = self._mpu.data_queue
        while not q.empty():
            try:
                q.get_nowait()
                q.task_done()
            except: break

    def _broadcast_loop(self) -> None:
        q = self._mpu.data_queue
        while self._is_running:
            try:
                data = q.get(timeout=0.5)
            except queue.Empty:
                continue

            with self._clients_lock:
                for conn, state in list(self._clients.items()):
                    if state["streaming"]:
                        try:
                            # 根據 Client 的遮罩過濾資料包
                            m = state["mask"]
                            filtered = {k: v for k, v in data.items() 
                                       if k in [f.name.lower() for f in MPUChannel if (m & f) and bin(f.value).count('1')==1]}
                            
                            if filtered:
                                payload = json.dumps(filtered).encode('utf-8') + b'\n'
                                conn.sendall(payload)
                        except (OSError, ConnectionResetError):
                            # 發送失敗也視同斷開，執行清理
                            self._remove_client(conn)
            q.task_done()

    def _remove_client(self, conn: socket.socket) -> None:
        with self._clients_lock:
            if conn in self._clients:
                try:
                    # 先從 Selector 取消註冊，防止重複觸發回呼
                    self._selector.unregister(conn)
                    conn.close()
                except: pass
                del self._clients[conn]
                logging.info("已移除 Client 並釋放資源")
        
        # 移除 Client 後務必重新檢查硬體狀態 (若無 Client 則停止執行緒)
        self._update_hardware()

    def run(self) -> None:
        self._is_running = True
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        
        logging.info("Selector 主迴圈啟動 (Non-blocking)")
        try:
            while self._is_running:
                events = self._selector.select(timeout=1.0)
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        self._is_running = False
        self._mpu.stop()
        self._selector.close()
        self._server_sock.close()
        logging.info("伺服器停止")

if __name__ == "__main__":
    mpu = MPU9250Buffer()
    server = MPUSocketServerNonBlocking(mpu)
# 定義訊號處理器
    def handle_exit(signum, frame):
        logging.info(f"接收到訊號 {signum}，正在關閉 Daemon...")
        server.stop() # 這會呼叫 mpu.stop() 關閉硬體執行緒與 Buffer
        sys.exit(0)

    # 註冊訊號
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    server.run()
