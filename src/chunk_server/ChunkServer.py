from concurrent.futures import ThreadPoolExecutor
import socket
import json

class ChunkServer:
    def __init__(self, host='localhost', port=6000, max_workers=10):
        
        
        # Networking & threading
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 over TCP
        self.server_socket.bind((self.host, self.port)) # Tells OS port is taken for incoming connections
        self.server_socket.listen(5) # Up to 5 concurrent connections, after 5, requests are queued
        self.executor = ThreadPoolExecutor(max_workers=max_workers) # create a managed thread pool

    def start(self):
        '''
        Start the ChunkServer
        '''
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"connected to {addr}")
            self.executor.submit(self.handle_request, client_socket)


    def handle_request(self, client_socket):
        try: 
            data = client_socket.recv(1024).decode()
            request = json.loads(data)  # Parse JSON request
            print(f"Received request: {request}")

            if request.get("request_type") == "UPLOAD_CHUNK":
                self.upload_chunk(client_socket)

            elif request.get("request_type") == "DOWNLOAD_CHUNK":
                 self.download_chunk(client_socket)

            # Handle other request types below

        except json.JSONDecodeError:
            print("Invalid JSON received")


        except Exception as e:
            print(f"Error handling request: {e}")
        
        finally:
            client_socket.close() # use this to close connction once finished 