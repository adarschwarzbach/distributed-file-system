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
        chunk_server_info = self.coordinator_connection.get_chunk_locations(file_id) # form [file_id: file_id, chunks: [{chunk_id, chunk_index, chunk_server_locations],...]
        print(chunk_server_info)
        chunks = chunk_server_info['chunks']


        futures = []
        downloaded_chunks = {}

        # Set up parallel downloads
        with ThreadPoolExecutor() as executor:
            for chunk in chunks:
                chunk_id = chunk["chunk_id"]
                chunk_index = chunk["chunk_index"]
                servers = chunk['chunk_server_locations']
                # Only schedule a download if there are servers for the chunk
                if len(servers) > 0:
                    # Attempt download from each server replica 
                    future = executor.submit(self.download_chunk_from_servers, chunk_id, chunk_index, servers)
                    futures.append(future)

            # Process download results
            for future in as_completed(futures):
                chunk_index, chunk_data = future.result()
                print('\n chunk_index', chunk_index)
                if chunk_data is not None:
                    downloaded_chunks[chunk_index] = chunk_data
                else:
                    print("Failed to download one or more chunks.")
                    return False

        # Reassemble file 
        self.assemble_file(file_id, downloaded_chunks, 'output.pdf') #replace file name
        print(f"File {file_id} downloaded and assembled successfully.")
        return True
        
    
    def download_chunk_from_servers(self, chunk_id: str, chunk_index: int, servers: List[Dict]):
        """Attempt to download a chunk from the list of servers in order"""
        for server_info in servers:
            server = ChunkServerConnection(self.user_id, server_info["chnk_srv_addr"], server_info["chnk_srv_port"], server_info["chnk_srv_id"])
            chunk_data = server.download_chunk(chunk_id)
            if chunk_data is not None:
                print(f"Downloaded chunk {chunk_id} from server {server.chunk_server_id}")
                return chunk_index, chunk_data
        print(f"Failed to download chunk {chunk_id} from all replicas.")
        return chunk_index, None


    def assemble_file(self, file_id: str, downloaded_chunks: Dict[int, bytes], output_file_name):
        print('\ndownloaded chunks', downloaded_chunks)
        indexes = downloaded_chunks.keys()
        sorted_indexes = sorted(indexes)
        with open(output_file_name, 'wb') as output_file:
            for index in sorted_indexes:
                binary_data = downloaded_chunks[index]
                output_file.write(binary_data)