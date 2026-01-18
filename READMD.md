# MPU9250 IIO 數據採集與遠端監控系統

由於 Pi 5不像 Pi 4有實作mpu9250 Sensor ,大部分都需要再device Tree上做修改

本專案實作了一個完整的嵌入式監控解決方案，從底層 Linux 核心設備樹配置、udev 權限管理、Systemd 守護進程，到上層的非阻塞式 Socket 伺服器與 PySide6 圖形介面。

## 核心特性

* 
**硬體自動化配置**：透過 Device Tree Overlay 啟用 Raspberry Pi 5 的 I2C-1 與中斷腳位 。


* **安全權限管理**：結合 udev 規則與 Systemd 權限隔離，確保服務以非 root 用戶（`mpuuser`）身份安全運行。
* **高效數據分發**：利用 Linux IIO 字元設備讀取數據，並透過非阻塞 Socket 同步分發至多個客戶端。
* **智慧資源監控**：伺服器會根據有無連線動態管理硬體讀取執行緒，降低系統負載。
* 現代化 GUI**：基於 PySide6 實現的跨平台客戶端，採 MVC 架構設計 。



---

## 檔案結構說明

| 檔案名稱 | 分類 | 說明 |
| --- | --- | --- |
| `mpu9250-pi5-overlay.dts` | 硬體配置 | <br>**設備樹源檔**：配置 I2C-1 地址 (0x68) 與 GPIO 23 中斷 。

 |
| `mpu_buffer.py` | 驅動封裝 | 處理 Sysfs 節點讀取、Scale/Offset 校正與 IIO Buffer 管理。 |
| `mpu_socket.py` | 後端服務 | 非阻塞式 Socket Server，處理 JSON 指令與數據廣播。 |
| `mpu_server.service` | 系統部署 | <br>**Systemd 服務設定**：配置權限隔離、自動重啟與路徑 。|
| `99-mydevices.rules` | 系統部署 | **udev 規則檔**：賦予 `mydevices` 群組存取 IIO 設備權限。 |
| `mpu9250_ui_app.py` | 前端應用 | 基於 PySide6 的 GUI 監控程式主邏輯 。 |
| `mpu9250.ui` | 前端應用 | 使用 Qt Designer 設計的介面描述檔 。 |
| `images/wiring.png` | 文件資源 | 硬體接線示意圖。 |

---

## 硬體接線說明 (Hardware Wiring)

本專案使用 Raspberry Pi 5 的 I2C-1 介面進行通訊 ，並利用 GPIO 23 接收感測器的 Data Ready 中斷訊號 。

![MPU9250 與 Raspberry Pi 5 接線圖](./images/wiring.png)

**接腳對應表：**

| MPU9250 腳位 | Raspberry Pi 5 實體腳位 (Physical Pin) | 功能說明 |
| --- | --- | --- |
| **VCC** | Pin 1 | 3.3V 電源 |
| **GND** | Pin 9 | 接地 (GND) |
| **SDA** | Pin 3 | I2C1 資料線 (SDA / GPIO 2)  |
| **SCL** | Pin 5 | I2C1 時脈線 (SCL / GPIO 3)  |
| **INT** | Pin 16 | 中斷觸發 (GPIO 23)  |

---

## 系統部署指南

### 1. 硬體啟動 (Device Tree)

將 `.dts` 編譯並套用：

```bash
dtc -@ -I dts -O dtb -o mpu9250-pi5.dtbo mpu9250-pi5-overlay.dts
sudo cp mpu9250-pi5.dtbo /boot/overlays/
# 編輯 /boot/firmware/config.txt 加入: dtoverlay=mpu9250-pi5

```

### 2. 權限與使用者設定 (udev)

```bash
sudo groupadd mydevices
sudo useradd -m -G mydevices mpuuser
sudo cp 99-mydevices.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

```

### 3. 守護進程部署 (Systemd)

```bash
sudo cp mpu_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mpu_server.service
sudo systemctl start mpu_server.service

```

---

## 驗證與操作 (GUI Verification)

部署完成後，可使用專屬的 GUI 客戶端 `mpu9250_ui_app.py` 驗證數據鏈路是否暢通。

### 操作步驟：

1. **啟動伺服器**：確保 Raspberry Pi 上的 `mpu_server.service` 已啟動。
2. **執行 GUI**：在您的電腦（需與 Pi 在同一區域網路）或 Pi 本機執行：
```bash
python3 mpu9250_ui_app.py

```


3. 
**連線設定** ：


* 在 `IP Address` 欄位輸入 Raspberry Pi 的 IP（預設 127.0.0.1）。


* 在 `PORT` 欄位輸入 8888 。


* 點擊 **START** 進行連線。


4. 
**數據訂閱** ：


* 勾選 UI 上的複選框（如 `acc_x`, `gyro_y` 等）。


* 系統會即時將 `config_channels` 指令送至伺服器 。


* 標籤內容（如 `mpu_acc_x`）應開始更新顯示感測器數值 。




5. 
**停止連線** ：


* 點擊 **END** 停止數據串流並斷開連線 。





---

## 通訊協定規範

伺服器與客戶端之間採用 **JSON over TCP**。

* **配置指令**：`{"action": "config_channels", "params": ["accel_x", "gyro_y"]}`。
* **串流控制**：`{"action": "start_send"}` 或 `{"action": "stop_send"}`。
* **數據推送**：`{"accel_x": 0.12, "gyro_y": -0.05}`。

---

## 技術亮點

* **非阻塞連線管理**：採用 `selectors` 模組實現高效的單執行緒多工處理，防止 I/O 阻塞。
* 
**MVC 隔離設計**：GUI 端將 `MPUModel`（通訊邏輯）與 `MainWindow`（視圖）分離，確保介面反應靈敏 。


* **強健性**：針對 Windows 端常見的 `ConnectionResetError` 進行了例外處理，確保伺服器穩定性。
# MPU9250 IIO Data Acquisition and Remote Monitoring System

**Unlike the Raspberry Pi 4, the Raspberry Pi 5 does not feature built-in implementation or default configurations for the MPU9250 sensor. Consequently, manual modifications to the Device Tree are required for most integration scenarios to ensure the hardware is correctly recognized by the kernel.**

This project implements a comprehensive embedded monitoring solution, spanning from low-level Linux kernel Device Tree configuration, udev permission management, and systemd daemons, up to a high-level non-blocking Socket server and a PySide6 graphical interface.

---

## Core Features

* 
**Automated Hardware Configuration**: Utilizes Device Tree Overlays to enable the I2C-1 interface and interrupt pins on the Raspberry Pi 5.


* 
**Secure Permission Management**: Combines udev rules with Systemd privilege isolation to ensure the service runs securely under a non-root user (`mpuuser`).


* **Efficient Data Distribution**: Reads data via Linux IIO character devices and synchronously distributes it to multiple clients using non-blocking sockets.
* **Smart Resource Monitoring**: The server dynamically manages hardware reading threads based on the presence of active connections, reducing system load.

---

## File Structure Description

| File Name | Category | Description |
| --- | --- | --- |
| `mpu9250-pi5-overlay.dts` | Hardware Config | <br>**Device Tree Source**: Configures I2C-1 address (0x68) and GPIO 23 interrupt.

 |
| `mpu_buffer.py` | Driver Wrapper | Handles Sysfs node reading, Scale/Offset correction, and IIO Buffer management. |
| `mpu_socket.py` | Backend Service | Non-blocking Socket Server handling JSON instructions and data broadcasting. |
| `mpu_server.service` | System Deployment | <br>**Systemd Service Config**: Configures privilege isolation, automatic restart, and execution paths.

 |
| `mpu9250_ui_app.py` | Frontend App | PySide6-based cross-platform GUI monitoring program.

 |

---

## Hardware Wiring Instructions

This project uses the Raspberry Pi 5's I2C-1 interface and GPIO 23 as an interrupt trigger. Please refer to the diagram below for hardware connection:

**Pinout Reference:**
![Wiring between MPU2950 and Raspberry Pi 5 ](./images/wiring.png)

| MPU9250 Pin | Raspberry Pi 5 Physical Pin (Header) | Function Description |
| --- | --- | --- |
| **VCC** | Pin 1 | 3.3V Power |
| **GND** | Pin 9 | Ground |
| **SDA** | Pin 3 | I2C1 Data Line (SDA) |
| **SCL** | Pin 5 | I2C1 Clock Line (SCL) |
| **INT** | Pin 16 | GPIO 23 (Interrupt Trigger) |

> **Note**: Please ensure the device is powered off before making any wire connections to avoid damaging the hardware.

---

## System Deployment Guide

### 1. Hardware Activation (Device Tree)

Compile and apply the `.dts` file to enable the hardware device:

```bash
dtc -@ -I dts -O dtb -o mpu9250-pi5.dtbo mpu9250-pi5-overlay.dts
sudo cp mpu9250-pi5.dtbo /boot/overlays/
# Add "dtoverlay=mpu9250-pi5" to /boot/firmware/config.txt

```

### 2. Permissions and User Setup (udev)

To allow non-root users access to IIO devices, udev rules and specific user groups must be configured.

* **Create Group and User**:
```bash
sudo groupadd mydevices
sudo useradd -m -G mydevices mpuuser

```


* **Set udev Rules** (Create `/etc/udev/rules.d/99-mpu9250.rules`):
```text
# Grant read/write access to IIO devices for the 'mydevices' group
SUBSYSTEM=="iio", GROUP="mydevices", MODE="0660"

```


After setting up the rule, execute: `sudo udevadm control --reload-rules && sudo udevadm trigger`

### 3. Daemon Deployment (Systemd)

This project implements privilege isolation via `mpu_server.service`:

* **Key Service Configuration**:
* 
**User/Group**: Set to `mpuuser` / `mydevices` to avoid running with root privileges.


* 
**WorkingDirectory**: The program runs in `/opt/mpu_project`.


* 
**ExecStart**: Points to `/opt/mpu_project/mpu_socket.py`.


* 
**Restart**: Set to `always` to ensure automatic restart within 5 seconds if the application crashes.




* **Start the Service**:
```bash
sudo cp mpu_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mpu_server.service
sudo systemctl start mpu_server.service

```



---

## Protocol Specification

Communication uses **JSON over TCP**.

* **Configure Channels** (Client -> Server): `{"action": "config_channels", "params": ["accel_x", "gyro_y"]}`
* **Data Format** (Server -> Client): `{"accel_x": 0.12, "gyro_y": -0.05}`

---

## Technical Highlights

* 
**Principle of Least Privilege**: By leveraging Systemd and udev, the program reads `/dev/iio:deviceX` directly without requiring root privileges, significantly enhancing system security.


* **Non-blocking Multiplexing**: Utilizes the `selectors` module to listen for client instructions and handle data distribution simultaneously within a single thread.
* **Robust Resource Management**: Ensures buffers and hardware threads are correctly closed via signal handlers when the service stops (SIGTERM/SIGINT).

License
    This project is licensed under the MIT License - see the LICENSE file for details.
