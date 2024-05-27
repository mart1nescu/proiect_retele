import socket
import threading
import sys

class SemaphoreClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.running = True
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()

    def send_command(self, command, semaphore_name):
        try:
            message = f"{command} {semaphore_name}"
            self.client_socket.send(message.encode())
        except Exception as e:
            print(f"Error communicating with server: {e}")

    def listen_for_messages(self):
        while self.running:
            try:
                response = self.client_socket.recv(1024).decode()
                if response:
                    self.clear_and_reprint_prompt(f"Server response: {response}")
            except (ConnectionResetError, BrokenPipeError):
                if self.running:
                    print("\rDisconnected from server")
                break
            except Exception as e:
                if self.running:
                    print(f"\rError receiving message from server: {e}")
                break
        print("Listener thread ending")

    def acquire_semaphore(self, semaphore_name):
        self.send_command("acquire", semaphore_name)

    def release_semaphore(self, semaphore_name):
        self.send_command("release", semaphore_name)

    def close_connection(self):
        self.running = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
        self.listener_thread.join()
        print("Connection closed and listener thread joined")

    def clear_and_reprint_prompt(self, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(message)
        sys.stdout.write("Enter 'acquire' to acquire semaphore or 'release' to release semaphore: ")
        sys.stdout.flush()

if __name__ == "__main__":
    client = SemaphoreClient()
    semaphore_name = "test_semaphore"

    try:
        while True:
            action = input("Enter 'acquire' to acquire semaphore or 'release' to release semaphore: ")
            if action == "acquire":
                client.acquire_semaphore(semaphore_name)
            elif action == "release":
                client.release_semaphore(semaphore_name)
            elif action == "exit":
                break
            else:
                print("Invalid command. Please enter 'acquire', 'release', or 'exit'.")
    finally:
        client.close_connection()
