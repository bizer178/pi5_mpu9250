from __future__ import annotations
import socket
import threading
import json
import time
from typing import Any

class MPUTestClient:
    _host: str
    _port: int
    _sock: socket.socket | None
    _is_running: bool
    _receive_thread: threading.Thread | None

    def __init__(self, host: str = "192.168.1.114", port: int = 8888) -> None:
        self._host = host
        self._port = port
        self._sock = None
        self._is_running = False
        self._receive_thread = None

    def connect(self) -> bool:
        """建立 Socket 連線"""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self._host, self._port))
            self._is_running = True
            
            # 啟動接收執行緒
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            print(f"[*] 已成功連線至 {self._host}:{self._port}")
            return True
        except ConnectionRefusedError:
            print("[!] 連線失敗：伺服器未啟動或連線數已滿")
            return False

    def send_cmd(self, action: str, params: list[str] | None = None) -> None:
        """發送 JSON 指令"""
        if not self._sock:
            return
        
        cmd = {
            "action": action,
            "params": params or []
        }
        try:
            # 必須加上 \n 作為訊息結尾
            payload = json.dumps(cmd).encode('utf-8') + b'\n'
            self._sock.sendall(payload)
            print(f"[Send] {cmd}")
        except Exception as e:
            print(f"[!] 發送指令失敗: {e}")

    def _receive_loop(self) -> None:
        """持續接收伺服器回傳的 JSON 資料"""
        buffer = ""
        while self._is_running and self._sock:
            try:
                data = self._sock.recv(4096).decode('utf-8')
                if not data:
                    print("[*] 伺服器已中斷連線")
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    try:
                        sensor_packet = json.loads(line)
                        # 格式化輸出資料
                        print(f"\r[Recv] {sensor_packet}", end="")
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                if self._is_running:
                    print(f"\n[!] 接收錯誤: {e}")
                break
        self._is_running = False

    def close(self) -> None:
        """關閉連線"""
        self._is_running = False
        if self._sock:
            self._sock.close()
            self._sock = None
        print("\n[*] 用戶端已關閉")

# --- 測試流程腳本 ---
if __name__ == "__main__":
    client = MPUTestClient()
    
    if client.connect():
        try:
            # 1. 配置通道 (例如：加速度 X, Y 與 陀螺儀 Z)
            client.send_cmd("config_channels", ["ACCEL_X", "ACCEL_Y", "GYRO_Z"])
            time.sleep(0.5)
            
            # 2. 開始接收串流
            print("\n[*] 請求啟動數據傳送...")
            client.send_cmd("start_send")
            
            # 模擬接收 5 秒鐘
            time.sleep(5)
            
            # 3. 測試動態更改通道 (例如改為只拿加速度)
            print("\n\n[*] 測試動態切換通道為 ACCEL_XYZ...")
            client.send_cmd("config_channels", ["ACCEL_XYZ"])
            time.sleep(3)
            
            # 4. 停止接收
            print("\n\n[*] 停止傳送數據...")
            client.send_cmd("stop_send")
            time.sleep(1)
            
            # 5. 中斷連線
            client.send_cmd("disconnect")
            
        except KeyboardInterrupt:
            pass
        finally:
            client.close()
