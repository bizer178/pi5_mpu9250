import sys
import time
import unittest
from PySide6.QtWidgets import QApplication
from mpu9250_ui_app import MPUModel

# Minimal app for QThread/Signals
app = QApplication(sys.argv)

class TestMPUModel(unittest.TestCase):
    def setUp(self):
        self.model = MPUModel()
        self.received_data = []
        self.connected = False
        
        self.model.connected.connect(self.on_connected)
        self.model.data_received.connect(self.on_data)
        
    def on_connected(self):
        self.connected = True
        
    def on_data(self, data):
        self.received_data.append(data)

    def test_connection_and_streaming(self):
        print("Connecting to mock server...")
        self.model.connect_server("127.0.0.1", 8888)
        
        # Wait for connection
        start = time.time()
        while not self.connected and time.time() - start < 2:
            app.processEvents()
            time.sleep(0.1)
            
        self.assertTrue(self.connected, "Failed to connect to mock server")
        print("Connected.")
        
        # Start streaming
        self.model.send_command("start_send")
        print("Sent start_send")
        
        # config channels (optional, but good practice per protocol)
        self.model.send_command("config_channels", ["accel_x", "gyro_z"])
        
        # Wait for data
        start = time.time()
        while len(self.received_data) < 5 and time.time() - start < 5:
            app.processEvents()
            time.sleep(0.1)
            
        self.assertGreater(len(self.received_data), 0, "No data received")
        print(f"Received {len(self.received_data)} packets")
        print(f"Sample packet: {self.received_data[0]}")
        
        # Verify packet structure (roughly)
        self.assertIn("accel_x", self.received_data[0])
        
        # Stop sending
        self.model.send_command("stop_send")
        self.model.disconnect_server()

if __name__ == "__main__":
    unittest.main()
