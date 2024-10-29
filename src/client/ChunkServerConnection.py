from typing import *
import socket
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import time

class ChunkServerConnection:
    def __init__(self, user_id, chnk_srv_addr, chnk_srv_port, chnk_srv_id, max_workers=4, max_retries=3):
        self.chnk_srv_addr = chnk_srv_addr
        self.chnk_srv_port = chnk_srv_port
        self.user_id = user_id
        self.chunk_server_id = chnk_srv_id
        self.max_workers = max_workers
        self.max_retries = max_retries
        

    # Need to abstract this into upload manager
    def chunk_file(self, file_location, chunk_size_mb, file_id):
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        futures = []
        all_success = True  

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            with open(file_location, 'rb') as file:
                chunk_index = 0

                while True:
                    chunk = file.read(chunk_size_bytes)
                    chunk_id = f"{file_id}_{uuid.uuid4()}"
                    if not chunk:
                        break

                    future = executor.submit(self.upload_chunk, chunk_id, chunk, chunk_index)
                    futures.append(future)

                    chunk_index += 1


            for future in as_completed(futures):
                success = future.result()
                if not success:
                    print("One or more chunks failed to upload after retries.")
                    all_success = False

        if all_success:
            print(f"File {file_id} uploaded successfully in {chunk_index} chunks.")
        else:
            print(f"File {file_id} upload encountered errors.")

        return all_success


    def upload_chunk(self, chunk_id, chunk_object, chunk_index) -> bool:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM)  as s:
                    s.connect((self.chnk_srv_addr, self.chnk_srv_port))

                    request = {
                        "request_type": "UPLOAD_CHUNK",
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,
                        "chunk_size": len(chunk_object),
                        "user_id": self.user_id
                    }
                    s.sendall(json.dumps(request).encode() + b"\n\n" + chunk_object)
                    print("Chunk upload request sent to server.")

                    data = s.recv(1024).decode()
                    response = json.loads(data)  # Parse JSON response

                    if response.get("status") == "success":
                        print(f"Chunk ID {chunk_id} successfully uploaded to ChunkServer at {self.chnk_srv_port}:{self.chnk_srv_addr}")
                        return True
                    else:
                        attempt += 1
                        print(f"Server error during chunk upload for {chunk_id}. Retry attempt {attempt}/{self.max_retries}")
                        time.sleep(1.2 ** attempt)  
                    
            except Exception as e:
                attempt += 1
                print(f"Connection error during chunk upload for {chunk_id}: {e}. Retry attempt {attempt}/{self.max_retries}")
                time.sleep(1 ** attempt)  
            
        print(f"Failed to upload chunk {chunk_id} after {self.max_retries} attempts.")
        return False

    
    def download_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM)  as s:
                s.connect((self.chnk_srv_addr, self.chnk_srv_port))

                request = {
                    "request_type": "DOWNLOAD_CHUNK",
                    "chunk_id": chunk_id,
                }
                s.sendall(json.dumps(request).encode())
                print("Chunk download request sent to server.")

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

                if response.get("status") == "success":
                    chunk_index = response.get("chunk_index")
                    chunk_data = response.get("chunk_data").encode()  # Ensure the chunk data is in bytes
                    print(f"Chunk ID {chunk_id} (index {chunk_index}) successfully downloaded.")
                    return chunk_index, chunk_data  # Return both chunk index and data
                else:
                    print(f"Error downloading chunk: {response.get('error')}")
                    return None, None

                
        except Exception as e:
            print(f"Error during chunk download: {e}")
            return None, None
        
