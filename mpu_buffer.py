from __future__ import annotations
import os
import struct
import threading
import queue
from enum import IntFlag, auto
from dataclasses import dataclass
from typing import Any, TypeAlias, Final

# 1. 定義通道 Flag
class MPUChannel(IntFlag):
    NONE = 0
    ACCEL_X = auto()
    ACCEL_Y = auto()
    ACCEL_Z = auto()
    GYRO_X = auto()
    GYRO_Y = auto()
    GYRO_Z = auto()
    MAGN_X = auto()
    MAGN_Y = auto()
    MAGN_Z = auto()
    
    ACCEL_XYZ = ACCEL_X | ACCEL_Y | ACCEL_Z
    GYRO_XYZ = GYRO_X | GYRO_Y | GYRO_Z
    MAGN_XYZ = MAGN_X | MAGN_Y | MAGN_Z
    ALL = ACCEL_XYZ | GYRO_XYZ | MAGN_XYZ

# 型別別名 (3.11 相容)
SensorData: TypeAlias = dict[str, float]
# 定義 Queue 的型別，這在 strict 模式下很重要
# Python 3.9+ 的 queue.Queue 支援泛型標註
SensorQueue: TypeAlias = "queue.Queue[SensorData]"

@dataclass
class ChannelMeta:
    name: str
    index: int
    scale: float
    offset: float

class MPU9250Buffer:
    _device_path: str
    _char_dev_path: str
    _running: bool
    _thread: threading.Thread | None
    _active_configs: list[ChannelMeta]
    _packet_format: str
    _packet_size: int
    # 外部訂閱用的 Queue
    _data_queue: SensorQueue

    def __init__(self, symlink_path: str = "/dev/mpu_9250", q_size: int = 100) -> None:
        if not os.path.exists(symlink_path):
            raise FileNotFoundError(f"Missing device: {symlink_path}")
        
        real_path = os.path.realpath(symlink_path)
        dev_name = os.path.basename(real_path)
        
        self._char_dev_path = real_path
        self._device_path = f"/sys/bus/iio/devices/{dev_name}"
        
        # 初始化 Queue，設定 maxsize 避免消費者當機導致記憶體溢位
        self._data_queue = queue.Queue(maxsize=q_size)
        
        self._running = False
        self._thread = None
        self._active_configs = []
        self._packet_format = ""
        self._packet_size = 0

    @property
    def data_queue(self) -> SensorQueue:
        """供外部獲取 Queue 實例以進行訂閱 (get)"""
        return self._data_queue

    def _get_sysfs_base_name(self, flag: MPUChannel) -> str:
        name = flag.name.lower() if flag.name else ""
        return name.replace("gyro", "anglvel")

    def config_channels(self, selection: MPUChannel) -> None:
        """配置通道，統一使用 Big Endian (>) 解析"""
        self._set_buffer_enable(0)
     
        temp_metas: list[ChannelMeta] = []
        for flag in MPUChannel:
            if flag == MPUChannel.NONE or bin(flag.value).count('1') > 1:
                continue
            
            sysfs_base = self._get_sysfs_base_name(flag)
            is_enabled = bool(selection & flag)
            
            self._write_sysfs(f"scan_elements/in_{sysfs_base}_en", 1 if is_enabled else 0)
            
            if is_enabled:
                idx_raw = self._read_sysfs(f"scan_elements/in_{sysfs_base}_index")
                if idx_raw is None: continue
                
                scale, offset = self._get_metadata(sysfs_base)
                temp_metas.append(ChannelMeta(
                    name=flag.name.lower() if flag.name else sysfs_base,
                    index=int(idx_raw),
                    scale=scale,
                    offset=offset
                ))

        temp_metas.sort(key=lambda m: m.index)
        self._active_configs = temp_metas
        
        # 使用 '>' Big Endian 解析
        self._packet_format = f">{'h' * len(self._active_configs)}"
        self._packet_size = struct.calcsize(self._packet_format)

        if self._running:
            self._set_buffer_enable(1)


    def _reader_loop(self) -> None:
        try:
            with open(self._char_dev_path, "rb") as dev:
                self._set_buffer_enable(1)
                while self._running:
                    raw_bytes = dev.read(self._packet_size)
                    if len(raw_bytes) < self._packet_size:
                        continue
                    
                    raw_ints = struct.unpack(self._packet_format, raw_bytes)
                    
                    data: SensorData = {}
                    for i, meta in enumerate(self._active_configs):
                        data[meta.name] = (float(raw_ints[i]) + meta.offset) * meta.scale
                    
                    # --- 發布到 Queue ---
                    try:
                        # 使用 block=False 配合 maxsize，如果 Queue 滿了就丟棄舊資料，確保即時性
                        self._data_queue.put_nowait(data)
                    except queue.Full:
                        try:
                            self._data_queue.get_nowait() # 移除最舊的一筆
                            self._data_queue.put_nowait(data)
                        except queue.Empty:
                            pass
        finally:
            self._set_buffer_enable(0)

    # --- 內部工具 ---
    def _get_metadata(self, name: str) -> tuple[float, float]:
        prefix = name.rsplit('_', 1)[0]
        s = self._read_sysfs(f"in_{name}_scale") or self._read_sysfs(f"in_{prefix}_scale") or "1.0"
        o = self._read_sysfs(f"in_{name}_offset") or self._read_sysfs(f"in_{prefix}_offset") or "0.0"
        return float(s), float(o)

    def _read_sysfs(self, subpath: str) -> str | None:
        p = os.path.join(self._device_path, subpath)
        if not os.path.exists(p): return None
        with open(p, "r") as f: return f.read().strip()

    def _write_sysfs(self, subpath: str, val: Any) -> None:
        with open(os.path.join(self._device_path, subpath), "w") as f:
            f.write(str(val))

    def _set_buffer_enable(self, state: int) -> None:
        self._write_sysfs("buffer/enable", state)

    def start(self) -> None:
        if not self._active_configs: return
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread: self._thread.join(1.0)

# --- 使用方式範例 ---
if __name__ == "__main__":
    imu = MPU9250Buffer()
    imu.config_channels(MPUChannel.ACCEL_XYZ | MPUChannel.GYRO_XYZ)
    imu.start()

    # 外部訂閱者 (可以是另一個執行緒)
    data_q = imu.data_queue
    try:
        while True:
            # 從 Queue 拿資料，這會阻塞直到有新資料
            sensor_packet = data_q.get() 
            print(f"收到即時數據: {sensor_packet}")
            # 處理完畢後標記工作完成
            data_q.task_done()
    except KeyboardInterrupt:
        imu.stop()
