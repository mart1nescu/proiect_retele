import socket
import threading
from collections import defaultdict

class SemaphoreServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.semaphores = defaultdict(lambda: {'owner': None, 'waiting': []})
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    print("Client disconnected")
                    client_socket.close()
                    break

                command, semaphore_name = message.split()
                if command == "acquire":
                    self.acquire_semaphore(client_socket, semaphore_name)
                elif command == "release":
                    self.release_semaphore(client_socket, semaphore_name)
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected")
                client_socket.close()
                break
            except Exception as e:
                print(f"Client handling error: {e}")
                client_socket.close()
                break

    def acquire_semaphore(self, client_socket, semaphore_name):
        with self.lock:
            semaphore = self.semaphores[semaphore_name]
            if semaphore['owner'] is client_socket:
                client_socket.send(f"You already own semaphore {semaphore_name}".encode())
            elif semaphore['owner'] is None:
                semaphore['owner'] = client_socket
                client_socket.send(f"Semaphore {semaphore_name} acquired".encode())
            else:
                if client_socket not in semaphore['waiting']:
                    semaphore['waiting'].append(client_socket)
                    client_socket.send(f"Semaphore {semaphore_name} busy, added to wait list".encode())
                else:
                    client_socket.send(f"Semaphore {semaphore_name} busy, already in wait list".encode())

    def release_semaphore(self, client_socket, semaphore_name):
        with self.lock:
            semaphore = self.semaphores[semaphore_name]
            if semaphore['owner'] == client_socket:
                if semaphore['waiting']:
                    next_client = semaphore['waiting'].pop(0)
                    semaphore['owner'] = next_client
                    try:
                        next_client.send(f"Semaphore {semaphore_name} acquired".encode())
                    except (ConnectionResetError, BrokenPipeError):
                        self.release_semaphore(next_client, semaphore_name)
                else:
                    semaphore['owner'] = None
                client_socket.send(f"Semaphore {semaphore_name} released".encode())
            else:
                client_socket.send(f"You do not own semaphore {semaphore_name}".encode())

    def run(self):
        try:
            while True:
                client_socket, _ = self.server_socket.accept()
                print("New client connected")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        except KeyboardInterrupt:
            print("Server shutting down")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = SemaphoreServer()
    server.run()
