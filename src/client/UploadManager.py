from typing import *
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
from src.client.CoordinatorConnection import CoordinatorConnection
from src.client.ChunkServerConnection import ChunkServerConnection


class UploadManager:
    '''Read, chunk and upload file''' 
    
    def __init__(self, coordinator_connection: CoordinatorConnection, user_id):
        self.chunk_server_map = {}
        self.coordinator_connection = coordinator_connection
        self.cache_path = Path.home() / '512_dfs_cache'
        self.cache_path.mkdir(parents=True, exist_ok=True)

        chunk_server_info = self.coordinator_connection.get_chunk_servers() # form [{chnk_srv_addr, chnk_srv_port, chnk_srv_id}, ...]
        self.chunk_servers = [
            ChunkServerConnection(user_id, server['chnk_srv_addr'], server['chnk_srv_port'], server['chnk_srv_id'])
            for server in chunk_server_info
        ]

        
    
    # Need to abstract this into upload manager
    def upload_file(self, file_location, chunk_size_mb, file_id):
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        futures = []
        all_success = True  
        chunk_metadata = []
        server_count = len(self.chunk_servers)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            with open(file_location, 'rb') as file:
                chunk_index = 0

                while True:
                    chunk = file.read(chunk_size_bytes)
                    if not chunk:
                        break

                    chunk_id = f"{file_id}_{uuid.uuid4()}"
                    server = self.chunk_servers[chunk_index % server_count]

                    future = executor.submit(server.upload_chunk, chunk_id, chunk, chunk_index)
                    futures.append(future)

                    chunk_metadata.append({"chunk_id": chunk_id, "chunk_index": chunk_index})

                    chunk_index += 1

            # Process upload results
            for future in as_completed(futures):
                success = future.result()
                if not success:
                    print("One or more chunks failed to upload after retries.")
                    all_success = False

        if all_success:
            print(f"File {file_id} uploaded successfully in {chunk_index} chunks.")
            self.save_metadata(file_id, chunk_metadata)
        else:
            print(f"File {file_id} upload encountered errors.")

        return all_success

        

    def save_metadata(self, file_id, chunk_metadata):
        """Save chunk metadata to a cache file"""
        metadata_file = self.cache_path / f"{file_id}_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(chunk_metadata, f, indent=4)
            print(f"Metadata for {file_id} saved at {metadata_file}.")
        except Exception as e:
            print(f"Failed to save metadata for {file_id}: {e}")

    




