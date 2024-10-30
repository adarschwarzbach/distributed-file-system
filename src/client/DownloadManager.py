from typing import *
import os
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.client.ChunkServerConnection import ChunkServerConnection
from src.client.CoordinatorConnection import CoordinatorConnection


class DownloadManager:
    '''
        Handle downloading, reassembling and writing files
    '''

    def __init__(self, coordinator_connection: CoordinatorConnection, user_id):
        self.coordinator_connection = coordinator_connection
        self.user_id = user_id
        self.cache_path = Path.home() / '512_dfs_cache'
        self.cache_path.mkdir(parents=True, exist_ok=True)

    
    def download_file(self, file_id):
        chunk_server_info = self.coordinator_connection.get_chunk_locations() # form [ {chunk_id:[{chnk_srv_addr, chnk_srv_port, chnk_srv_id,}, {replica_2}, {replica_3}], ...]

        metadata_file = self.cache_path / f"{file_id}_metadata.json"
        if not metadata_file.is_file():
            print(f"Metadata file {metadata_file} does not exist.")
            return False
        with open(metadata_file, 'r') as f:
            chunk_metadata = json.load(f)


        futures = []
        downloaded_chunks = {}

        # Set up parallel downloads
        with ThreadPoolExecutor() as executor:
            for chunk_info in chunk_metadata:
                chunk_id = chunk_info["chunk_id"]
                chunk_index = chunk_info["chunk_index"]
                servers_with_chunk = chunk_server_info.get(chunk_id, [])

                # Only schedule a download if there are servers for the chunk
                if servers_with_chunk:
                    # Attempt download from each server replica in order
                    future = executor.submit(self.download_chunk_from_servers, chunk_id, chunk_index, servers_with_chunk)
                    futures.append(future)

            # Process download results
            for future in as_completed(futures):
                chunk_index, chunk_data = future.result()
                if chunk_data is not None:
                    downloaded_chunks[chunk_index] = chunk_data
                else:
                    print("Failed to download one or more chunks.")
                    return False

        # Reassemble file 
        self.assemble_file(file_id, downloaded_chunks)
        print(f"File {file_id} downloaded and assembled successfully.")
        return True
        
    
    def download_chunk_from_servers(self, chunk_id: str, chunk_index: int, servers: List[Dict]):
        """Attempt to download a chunk from the list of servers in order"""
        for server_info in servers:
            server = ChunkServerConnection(self.user_id, server_info["chnk_srv_addr"], server_info["chnk_srv_port"], server_info["chnk_srv_id"])
            chunk_index, chunk_data = server.download_chunk(chunk_id)
            if chunk_data is not None:
                print(f"Downloaded chunk {chunk_id} from server {server.chunk_server_id}")
                return chunk_index, chunk_data
        print(f"Failed to download chunk {chunk_id} from all replicas.")
        return chunk_index, None


    def assemble_file(self, file_id: str, downloaded_chunks: Dict[int, bytes]):
        """Assemble chunks in order and write to the final file"""
        output_file = self.cache_path / f"{file_id}_assembled.mov"
        with open(output_file, 'wb') as f:
            for chunk_index in sorted(downloaded_chunks.keys()):
                f.write(downloaded_chunks[chunk_index])
        print(f"File {file_id} assembled and saved to {output_file}.")