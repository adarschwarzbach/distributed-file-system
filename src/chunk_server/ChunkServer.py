from concurrent.futures import ThreadPoolExecutor
import socket
import json
import os


class ChunkServer:
    def __init__(self, host='localhost', port=6000, max_workers=10):
        
        self.chunk_map = {} #map chunk_ids to file paths

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

            elif request.get('request_type') == 'HEALTH_CHECK':
                self.respond_health_check(client_socket)
            # Handle other request types below

        except json.JSONDecodeError:
            print("Invalid JSON received")


        except Exception as e:
            print(f"Error handling request: {e}")
        
        finally:
            client_socket.close() # use this to close connction once finished 
    
    def upload_chunk(self, client_socket):
        try:
            metadata = client_socket.recv(1024).decode()
            metadata = json.loads(metadata)

            file_name = metadata.get("file_name")  
            chunk_size = metadata.get("chunk_size") 

            if not file_name or not chunk_size:
                raise ValueError("Invalid metadata received.")

            print(f"Receiving chunk for file {file_name} (Size: {chunk_size} bytes)")

            file_path = f"./chunks/{file_name}"

            # Ensure the chunks directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Open a file to write the incoming data
            with open(file_path, "wb") as chunk_file:
                received_data = 0
                while received_data < chunk_size:
                    buffer = client_socket.recv(1024)  # Receive in 1024-byte chunks
                    if not buffer:
                        break
                    chunk_file.write(buffer)
                    received_data += len(buffer)

            if received_data != chunk_size:
                raise ValueError("Incomplete data received.")

            # Update the chunk map
            self.chunk_map[file_name] = file_path

            print(f"Chunk for file {file_name} saved successfully at {file_path}.")
            client_socket.send(json.dumps({"status": "SUCCESS", "file_name": file_name, "file_path": file_path}).encode())

        except Exception as e:
            print(f"Error uploading chunk: {e}")
            client_socket.send(json.dumps({"status": "FAILURE", "error": str(e)}).encode())
            

    def download_chunk(self, client_socket):
        pass
    
    def respond_health_check(self, client_socket):
        try:
            response = {"status": "OK"}
            client_socket.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Error sending health check response: {e}")
    
    def replicate_chunks(self, chunk_id, chunk_socket):
        #replicate chunk to other ChunkServers
        pass