from concurrent.futures import ThreadPoolExecutor
import socket
import json
import os
import time
import uuid
import base64
from pathlib import Path


class ChunkServer:
    def __init__(self, host='localhost', port=5000, max_workers=10):
        
        self.chunk_map = {} #map chunk_ids to file paths
        self.id = uuid.uuid4()
        # Networking & threading
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 over TCP
        self.server_socket.bind((self.host, self.port)) # Tells OS port is taken for incoming connections
        self.server_socket.listen(5) # Up to 5 concurrent connections, after 5, requests are queued
        self.executor = ThreadPoolExecutor(max_workers=max_workers) # create a managed thread pool

        self.coord_host = 'localhost'
        self.coord_port = 6000

        self.known_chunk_servers = set()

    def connect_to_coordinator(self):
        try:
            coord_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            coord_socket.connect((self.coord_host, self.coord_port))
            print(f"Connected to coordinator at {self.coord_host}:{self.coord_port}")

            registration_data = {
                "request_type": "REGISTER_CHUNK_SERVER",
                "chunk_server_id": str(self.id),
                "host": self.host,
                "port": self.port
            }
            coord_socket.sendall(json.dumps(registration_data).encode())
            response = coord_socket.recv(1024).decode()
            print(f"Coordinator response: {response}")
        except Exception as e:
            print(f"Failed to connect to coordinator: {e}")

    def start(self):
        print('started chunk server')
        self.connect_to_coordinator()
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"connected to {addr}")
            self.executor.submit(self.handle_request, client_socket)


    def handle_request(self, client_socket):
        try:
            # Buffer data until delimiter is detected
            data = ""
            while True:
                part = client_socket.recv(1024).decode()
                if not part:
                    break
                data += part
                if "\n\n" in data:
                    data = data.replace("\n\n", "")
                    break

            # Parse JSON request
            request = json.loads(data)
            print('request', request)

            if request.get("request_type") == "UPLOAD_CHUNK":
                self.upload_chunk(request, client_socket)

            elif request.get("request_type") == "DOWNLOAD_CHUNK":
                chunk_id = request.get('chunk_id')
                self.download_chunk(chunk_id, client_socket)

            elif request.get("request_type") == "HEALTH_CHECK":
                self.respond_health_check(client_socket)

        except json.JSONDecodeError:
            print("Invalid JSON received")

        except Exception as e:
            print(f"Error handling request: {e}")

        finally:
            client_socket.close()

    
    def upload_chunk(self, request, client_socket):
        try:
            #Upload chunk to memory
            chunk_id =  os.path.basename(request.get("chunk_id"))  # Ensure chunk_id is a simple identifier
            chunk_size = request.get("chunk_size")
            chunk_data_base64 = request.get("chunk_data")

            if not chunk_id or not chunk_size or not chunk_data_base64:
                raise ValueError("Invalid request received.")

            chunk_data = base64.b64decode(chunk_data_base64)

            print(f"Receiving chunk of chunk_id: {chunk_id} (Size: {chunk_size} bytes)")

            self.chunk_path = Path.home() / '512_chunk_path'
            self.chunk_path.mkdir(parents=True, exist_ok=True)
            chunk_file_path = self.chunk_path / f"{str(self.id)[:6]}_{chunk_id}.bin"  # Use .bin for a viewable binary file

            with open(chunk_file_path, "wb") as chunk_file:
                chunk_file.write(chunk_data)

            self.chunk_map[chunk_id] = str(chunk_file_path)

            print(f"Chunk for chunk_id {chunk_id} saved successfully at {chunk_file_path}.")
            client_socket.send(json.dumps({"status": "SUCCESS"}).encode())

            #Notify Coordinator that we successfully uploaded a chunk
            coord_req = {
                'request_type': 'CHUNK_UPLOAD_SUCCESS',
                'chunk_id': chunk_id,
                'chunk_server_id': str(self.id)
            }
            coord_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            coord_socket.connect((self.coord_host, self.coord_port))
            coord_socket.send(json.dumps(coord_req).encode())

            #OPTIONAL: Replicate Chunk to other ChunkServers
            replicate = request.get('replicate')
            if not replicate or replicate is None:
                return
            chunk_server_request = {
                'request_type': 'UPLOAD_CHUNK',
                'chunk_id': chunk_id,
                'chunk_size': chunk_size,
                'chunk_data': chunk_data_base64,
                'replicate': False
            }
            self.replicate_chunk_on_upload(chunk_server_request)

        except Exception as e:
            print(f"Error uploading chunk: {e}")
            client_socket.send(json.dumps({"status": "FAILURE", "error": str(e)}).encode())


            #HAD THIS BEFORE I REALIZED I COULD UPDATE COORDINATE VIA CLIENT AFTER EVERYTHING
            #notify coordinator that this specific chunk server stored a specific chunk for a specific file
            #coordinator_notification = {
            #    "request_type": "NOTIFY_COORDINATOR_OF_CHUNK_LOCATION",
            #    'chunk_server_id': self.id,
             #   "chunk_id": chunk_id,
            #    'file_id': file_id
            #    }
           # self.coord_socket.sendall(json.dumps(coordinator_notification).encode())

            

    def download_chunk(self, chunk_id, client_socket):
        try:
            file_path = self.chunk_map[chunk_id]
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Chunk with ID {chunk_id} not found.")

            print(f"Sending chunk with ID {chunk_id} from {file_path}")

            with open(file_path, "rb") as chunk_file:
                binary_data = chunk_file.read()

            client_socket.sendall(binary_data)

            print(f"Chunk with ID {chunk_id} sent successfully.")
            #client_socket.send(json.dumps({"status": "SUCCESS", "chunk_id": chunk_id}).encode())


        except Exception as e:
            print(f"Error downloading chunk: {e}")
            client_socket.send(json.dumps({"status": "FAILURE", "error": str(e)}).encode()) 
        pass
    
    def respond_health_check(self, client_socket):
        try:
            response = {"status": "OK"}
            client_socket.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Error sending health check response: {e}")
    

    #Replicate chunk on upload to 2 other ChunkServers
    def replicate_chunk_on_upload(self, chunk_server_req):
        num_replications = 0
        for other_chunk_server_addr, other_chunk_server_port in self.known_chunk_servers:
            if num_replications >=2:
                return
            num_replications += 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((other_chunk_server_addr, other_chunk_server_port))
                    s.sendall((json.dumps(chunk_server_req) + "\n\n").encode())
            except Exception as e:
                print(f'Error replicate chunk: {e}')

    #Replicate a chunk by request of Coordinator
    def replicate_chunk_from_download(self, chunk_id, chnk_srv_addr, chnk_srv_port):
        #replicate chunk to other ChunkServers
        try:
            #Download data to replicate
            file_path = self.chunk_map[chunk_id]
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Chunk with ID {chunk_id} not found.")

            print(f"Sending chunk with ID {chunk_id} from {file_path}")

            with open(file_path, "rb") as chunk_file:
                binary_data = chunk_file.read()

            #Send downloaded data to ChunkServer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((chnk_srv_addr, chnk_srv_port))
                    chunk_data_base64 = base64.b64encode(binary_data).decode('utf-8')

                    request = {
                        "request_type": "UPLOAD_CHUNK",
                        "chunk_id": chunk_id,
                        "chunk_size": len(binary_data),
                        "chunk_data": chunk_data_base64,
                        'replicate': False
                    }
                    s.sendall((json.dumps(request) + "\n\n").encode())

                    data = ""
                    while True:
                        part = s.recv(1024).decode()
                        if not part:
                            break
                        data += part
                        if "\n\n" in data:
                            data = data.replace("\n\n", "")
                            break

                    response = json.loads(data)  # Parse JSON response

                    if response.get("status") == "SUCCESS":
                        print(f"Chunk ID {chunk_id} successfully uploaded to ChunkServer at {self.chnk_srv_port}:{self.chnk_srv_addr}")
                        return True
                    elif response.get("status") == "FAILURE":
                        print(f"Server error during chunk upload for {chunk_id}. Retry attempt: Error: {response.get('error')}")
                        time.sleep(1.2)

        except Exception as e:
            print(f"Error downloading chunk: {e}")
        
        

