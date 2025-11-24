import cv2
import queue
import threading
import socket
import pickle

class DiamondDiffusionServer:
    def __init__(self, host='localhost', port=12345, debug=False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.debug = debug  # Debug mode
        self.image_queue = queue.Queue()  # Queue for debug images

        if self.debug:
            threading.Thread(target=self.show_images, daemon=True).start()  # Start GUI thread

        print(f"Server listening on {host}:{port}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            client_socket, addr = self.sock.accept()
            print(f"Accepted connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        try:
            while True:
                size_data = client_socket.recv(4)
                if not size_data:
                    print("Client disconnected.")
                    break

                size = int.from_bytes(size_data, 'big')
                data = b""
                while len(data) < size:
                    packet = client_socket.recv(size - len(data))
                    if not packet:
                        raise ConnectionResetError("Connection closed prematurely.")
                    data += packet

                compressed = pickle.loads(data)
                image_array = cv2.imdecode(compressed, cv2.IMREAD_COLOR)
                print(f"Received image of shape: {image_array.shape}")

                # Add image to debug queue
                if self.debug:
                    self.image_queue.put(image_array)
        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            client_socket.close()
            print("Closed client connection.")

    def show_images(self):
        while True:
            if not self.image_queue.empty():
                image = self.image_queue.get()
                cv2.imshow("Received Image", image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Exiting debug display.")
                    self.debug = False
                    cv2.destroyAllWindows()
                    break


if __name__ == '__main__':
    server = DiamondDiffusionServer(debug=True)
    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Shutting down server.")
        server.sock.close()
        cv2.destroyAllWindows()
