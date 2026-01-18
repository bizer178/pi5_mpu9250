import socket
import json
import time
import random
import threading

class MockServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.running = True
        self.clients = []
        print(f"Mock Server listening on {host}:{port}")

    def run(self):
        threading.Thread(target=self.accept_clients, daemon=True).start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def accept_clients(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"Connected by {addr}")
                self.clients.append(conn)
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except OSError:
                break

    def handle_client(self, conn):
        streaming = False
        try:
            while self.running:
                # Basic non-blocking check or loop
                conn.settimeout(0.1)
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    
                    # Process commands
                    buffer = data.decode('utf-8')
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        try:
                            cmd = json.loads(line)
                            print(f"Received: {cmd}")
                            if cmd['action'] == 'start_send':
                                streaming = True
                            elif cmd['action'] == 'stop_send':
                                streaming = False
                            elif cmd['action'] == 'disconnect':
                                return # Close connection
                        except json.JSONDecodeError:
                            pass
                except socket.timeout:
                    pass

                if streaming:
                    # Construct dummy data based on MPUChannel names
                    # We send everything for simplicity, the client filters normally, 
                    # but here let's just send a full set.
                    data_packet = {
                        "accel_x": random.uniform(-2, 2),
                        "accel_y": random.uniform(-2, 2),
                        "accel_z": random.uniform(-2, 2),
                        "anglvel_x": random.uniform(-250, 250), # gyro
                        "anglvel_y": random.uniform(-250, 250),
                        "anglvel_z": random.uniform(-250, 250),
                        "magn_x": random.uniform(-50, 50),
                        "magn_y": random.uniform(-50, 50),
                        "magn_z": random.uniform(-50, 50),
                    }
                    payload = json.dumps(data_packet).encode('utf-8') + b'\n'
                    conn.sendall(payload)
                    time.sleep(0.1) 
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            print("Client disconnected")
            if conn in self.clients:
                self.clients.remove(conn)
            conn.close()

    def stop(self):
        self.running = False
        self.server_socket.close()

if __name__ == '__main__':
    server = MockServer()
    server.run()
