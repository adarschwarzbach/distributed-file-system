from concurrent.futures import ThreadPoolExecutor
import socket

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
            request = client_socket.recv(1024).decode()
            print(f"Recieved request: {request}")
            if request == "GET_FILE":
                self.handle_get_client_id(client_socket)

            # Handle other request types below

        except Exception as e:
            print(f"Error handling request: {e}")
        
        finally:
            client_socket.close() # use this to close connction once finished 