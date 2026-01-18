import sys
import socket
import json
import threading
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, QThread

from mpu9250_ui import Ui_MainWindow

# --- Model ---
class MPUModel(QObject):
    connected = Signal()
    disconnected = Signal()
    data_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._socket = None
        self._running = False
        self._thread = None
        self.ip = "127.0.0.1"
        self.port = 8888

    def connect_server(self, ip, port):
        if self._running:
            return

        self.ip = ip
        self.port = port
        self._running = True
        
        # Start connection in a separate thread to avoid freezing UI
        self._thread = threading.Thread(target=self._socket_worker, daemon=True)
        self._thread.start()

    def disconnect_server(self):
        self._running = False
        if self._socket:
            try:
                # Send polite disconnect message
                self.send_command("disconnect")
                time.sleep(0.1)
                self._socket.close()
            except:
                pass
            self._socket = None
        # Signal will be emitted by the worker when loop exits

    def send_command(self, action, params=None):
        if not self._socket:
            return
        
        cmd = {"action": action}
        if params is not None:
            cmd["params"] = params
            
        try:
            msg = json.dumps(cmd) + "\n"
            self._socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            self.error_occurred.emit(f"Send Error: {e}")
            self.disconnect_server()

    def _socket_worker(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0) # Connection timeout
            self._socket.connect((self.ip, self.port))
            self._socket.settimeout(None) # Reset for blocking reads (or handle non-blocking)
            
            self.connected.emit()
            
            # Read loop
            buffer = ""
            while self._running:
                try:
                    data = self._socket.recv(4096)
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8', errors='ignore')
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip(): continue
                        
                        try:
                            # Try parsing as JSON data
                            data_dict = json.loads(line)
                            self.data_received.emit(data_dict)
                        except json.JSONDecodeError:
                            pass # or log it
                            
                except OSError as e:
                    if self._running: # If we didn't intentionally stop
                        self.error_occurred.emit(str(e))
                    break
        except Exception as e:
            self.error_occurred.emit(f"Connection Failed: {e}")
        finally:
            self._running = False
            self.disconnected.emit()
            if self._socket:
                self._socket.close()
                self._socket = None


# --- Controller ---
class MPUController:
    def __init__(self, model: MPUModel, view):
        self.model = model
        self.view = view
        
        # Connect View -> Controller -> Model
        self.view.ui.pushButton_start.clicked.connect(self.on_start_clicked)
        self.view.ui.pushButton_end.clicked.connect(self.on_end_clicked)
        
        # Connect Checkboxes
        self.checkbox_map = {
            self.view.ui.checkBox_acc_x: "accel_x",
            self.view.ui.checkBox_acc_y: "accel_y",
            self.view.ui.checkBox_acc_z: "accel_z",
            self.view.ui.checkBox_angval_x: "gyro_x", # converted from angval -> gyro in protocol
            self.view.ui.checkBox_angval_y: "gyro_y",
            self.view.ui.checkBox_angval_z: "gyro_z",
            self.view.ui.checkBox_mag_x: "magn_x",
            self.view.ui.checkBox_max_y: "magn_y", # Note: UI Object Name typo in provided file (checkBox_max_y -> mag_y)
            self.view.ui.checkBox_mag_z: "magn_z",
        }
        
        for cb, name in self.checkbox_map.items():
            cb.toggled.connect(self.on_config_changed)
            
        # Connect Model -> Controller/View
        self.model.connected.connect(self.on_connected)
        self.model.disconnected.connect(self.on_disconnected)
        self.model.data_received.connect(self.on_data_received)
        self.model.error_occurred.connect(self.on_error)

    def on_start_clicked(self):
        ip = self.view.ui.lineEdit_IP_Address.text()
        try:
            port = int(self.view.ui.lineEdit_PORT.text())
        except ValueError:
            QMessageBox.warning(self.view, "Error", "Port must be an integer")
            return
            
        self.view.ui.pushButton_start.setEnabled(False)
        self.view.update_status("Connecting...")
        self.model.connect_server(ip, port)

    def on_end_clicked(self):
        self.model.send_command("stop_send")
        self.model.disconnect_server()

    def on_connected(self):
        self.view.update_status("Connected")
        self.view.ui.pushButton_end.setEnabled(True)
        # Send initial config based on checkboxes
        self.send_current_config()
        # Start streaming
        self.model.send_command("start_send")

    def on_disconnected(self):
        self.view.update_status("Disconnected")
        self.view.ui.pushButton_start.setEnabled(True)
        self.view.ui.pushButton_end.setEnabled(False)

    def on_error(self, msg):
        self.view.update_status(f"Error: {msg}")
        # Logic to reset buttons on error is handled by on_disconnected calls
        # usually errors lead to socket closing

    def on_config_changed(self):
        # Only send config if we are connected
        if self.model._running:
            self.send_current_config()

    def send_current_config(self):
        params = []
        for cb, name in self.checkbox_map.items():
            if cb.isChecked():
                params.append(name)
        self.model.send_command("config_channels", params)

    def on_data_received(self, data):
        # Map data keys back to labels
        # Data keys from server (based on MPUChannel names): accel_x, anglvel_x, magn_x etc.
        # Note: server sends 'anglvel' but our protocol request was 'gyro'. 
        # The sensor buffer returns sysfs names.
        
        # View Labels Map
        label_map = {
            "accel_x": self.view.ui.label_mpu_acc_x,
            "accel_y": self.view.ui.label_mpu_acc_y,
            "accel_z": self.view.ui.label_mpu_acc_z,
            
            # Server returns 'anglvel' for gyro
            "gyro_x": self.view.ui.label_mpu_angval_x, 
            "gyro_y": self.view.ui.label_mpu_angval_y,
            "gyro_z": self.view.ui.label_mpu_angval_z,
            
            "magn_x": self.view.ui.label_mpu_mag_x,
            "magn_y": self.view.ui.label_mpu_mag_y,
            "magn_z": self.view.ui.label_mpu_mag_z,
        }

        for key, value in data.items():
            if key in label_map:
                label_map[key].setText(f"{value:.2f}")


# --- View ---
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialize default values
        self.ui.lineEdit_IP_Address.setText("127.0.0.1")
        self.ui.lineEdit_PORT.setText("8888")
        
        self.model = MPUModel()
        self.controller = MPUController(self.model, self)

    def update_status(self, text):
        self.ui.label_status.setText(text)

    def closeEvent(self, event):
        self.model.disconnect_server()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
