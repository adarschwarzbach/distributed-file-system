from typing import *
import socket
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import base64


class ChunkServerConnection:
    def __init__(self, user_id, chnk_srv_addr, chnk_srv_port, chnk_srv_id, max_workers=4, max_retries=3):
        self.chnk_srv_addr = chnk_srv_addr
        self.chnk_srv_port = chnk_srv_port
        self.user_id = user_id
        self.chunk_server_id = chnk_srv_id
        self.max_workers = max_workers
        self.max_retries = max_retries
        


    def upload_chunk(self, chunk_id, chunk_object, chunk_index, file_id) -> bool:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.chnk_srv_addr, self.chnk_srv_port))

                    # Encode chunk data (binary) to Base64
                    chunk_data_base64 = base64.b64encode(chunk_object).decode('utf-8')

                    # Create JSON request
                    request = {
                        "request_type": "UPLOAD_CHUNK",
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,
                        "chunk_size": len(chunk_object),
                        "user_id": self.user_id,
                        "file_id": file_id,
                        "chunk_data": chunk_data_base64
                    }

                    # Append delimiter and send
                    s.sendall((json.dumps(request) + "\n\n").encode())
                    print("Chunk upload request sent to server.")

                    # Receive and parse server response
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
                        attempt += 1
                        print(f"Server error during chunk upload for {chunk_id}. Retry attempt {attempt}/{self.max_retries}. Error: {response.get('error')}")
                        time.sleep(1.2 ** attempt)
                    else:
                        print("Error parsing status")

            except Exception as e:
                attempt += 1
                print(f"Connection error during chunk upload for {chunk_id}: {e}. Retry attempt {attempt}/{self.max_retries}")
                time.sleep(1 ** attempt)

        print(f"Failed to upload chunk {chunk_id} after {self.max_retries} attempts.")
        return False


    
    def download_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.chnk_srv_addr, self.chnk_srv_port))

                # Prepare and send the download request
                request = {
                    "request_type": "DOWNLOAD_CHUNK",
                    "chunk_id": chunk_id,
                }
                s.sendall((json.dumps(request) + "\n\n").encode())  # Add delimiter for message clarity
                print("Chunk download request sent to server.")

                # Buffer to collect incoming data
                data = b""
                while True:
                    part = s.recv(4096)  # Read in 4KB chunks
                    if not part:  # Break if the connection is closed
                        break
                    data += part
                    if b"\n\n" in data:  # Detect the end of the response
                        data = data.replace(b"\n\n", b"")  # Remove the delimiter
                        break

                # Parse the received data
                #response = json.loads(data.decode())  # Decode and parse JSON response

                #if response.get("status") == "SUCCESS":
                    # Decode the base64 chunk data back to bytes
                    #chunk_index = response.get("chunk_index")
                    #chunk_data_base64 = response.get("chunk_data")
                chunk_data = base64.b64decode(data)

                print(f"Chunk ID {chunk_id} successfully downloaded.")
                return chunk_data  
                #else:
                    #print(f"Error downloading chunk: {response.get('error')}")
                    #return None, None

        except Exception as e:
            print(f"Error during chunk download: {e}")
            return None, None

    
    
