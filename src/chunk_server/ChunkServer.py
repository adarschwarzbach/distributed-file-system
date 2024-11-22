from concurrent.futures import ThreadPoolExecutor
import socket
import json
import os
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
        self.coord_socket = None 

    def connect_to_coordinator(self):
        try:
            self.coord_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.coord_socket.connect((self.coord_host, self.coord_port))
            print(f"Connected to coordinator at {self.coord_host}:{self.coord_port}")

            registration_data = {
                "request_type": "REGISTER_CHUNK_SERVER",
                "chunk_server_id": str(self.id),
                "host": self.host,
                "port": self.port
            }
            self.coord_socket.sendall(json.dumps(registration_data).encode())
            response = self.coord_socket.recv(1024).decode()
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

            if request.get("request_type") == "UPLOAD_CHUNK":
                self.upload_chunk(request, client_socket)

            elif request.get("request_type") == "DOWNLOAD_CHUNK":
                self.download_chunk(request, client_socket)

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
            # Extract metadata and chunk data from request
            chunk_id =  os.path.basename(request.get("chunk_id"))  # Ensure chunk_id is a simple identifier
            chunk_size = request.get("chunk_size")
            chunk_data_base64 = request.get("chunk_data")
            file_id = request.get("file_id")

            if not chunk_id or not chunk_size or not chunk_data_base64:
                raise ValueError("Invalid request received.")

            # Decode Base64-encoded chunk data to binary
            chunk_data = base64.b64decode(chunk_data_base64)

            print(f"Receiving chunk of chunk_id: {chunk_id} (Size: {chunk_size} bytes)")

            self.chunk_path = Path.home() / '512_chunk_path'
            self.chunk_path.mkdir(parents=True, exist_ok=True)
            chunk_file_path = self.chunk_path / f"{chunk_id}.bin"  # Use .bin for a viewable binary file

            # Write the binary chunk data to the file
            with open(chunk_file_path, "wb") as chunk_file:
                chunk_file.write(chunk_data)

            # Update the chunk map with the new chunk
            self.chunk_map[chunk_id] = str(chunk_file_path)

            print(f"Chunk for chunk_id {chunk_id} saved successfully at {chunk_file_path}.")
            client_socket.send(json.dumps({"status": "SUCCESS"}).encode())


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

        except Exception as e:
            print(f"Error uploading chunk: {e}")
            client_socket.send(json.dumps({"status": "FAILURE", "error": str(e)}).encode())
            

    def download_chunk(self, client_socket):
        try:
            metadata = client_socket.recv(1024).decode()
            metadata = json.loads(metadata)

            chunk_id = metadata.get("chunk_id")  
            file_path = self.chunk_map[chunk_id]

            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Chunk with ID {chunk_id} not found.")

            print(f"Sending chunk with ID {chunk_id} from {file_path}")

            with open(file_path, "rb") as chunk_file:
                while True:
                    buffer = chunk_file.read(1024)  # Read in 1024-byte chunks
                    if not buffer:
                        break
                    client_socket.send(buffer)

            print(f"Chunk with ID {chunk_id} sent successfully.")
            client_socket.send(json.dumps({"status": "SUCCESS", "chunk_id": chunk_id}).encode())


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
    
    def replicate_chunks(self, chunk_id, chunk_socket):
        #replicate chunk to other ChunkServers
        pass









    # /Users/adarschwarzbach/Downloads/Bytebytego_Big_Archive_System_Design_2023.pdf