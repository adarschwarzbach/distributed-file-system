from typing import Dict, Set, List
from src.coordinator.File import File
from src.coordinator.ChunkServer import ChunkServer
from src.coordinator.Chunk import Chunk
import socket
from concurrent.futures import ThreadPoolExecutor
import uuid 
import json


class Coordinator:
    def __init__(self, host='localhost', port=6000, max_workers=10):
        # maps file_id to a File object
        file_map: Dict[int, File] = {}
        # maps chunk_id to the 3 ChunkServers where we can find that chunk
        chunk_map: Dict[int, List[ChunkServer]] = {}
        # dict of ChunkServers that are online mapping to the number of chunks on that chunk server
        active_chunkservers: Dict[ChunkServer, int] = {}

        # Networking & threading
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 over TCP
        self.server_socket.bind((self.host, self.port)) # Tells OS port is taken for incoming connections
        self.server_socket.listen(5) # Up to 5 concurrent connections, after 5, requests are queued
        self.executor = ThreadPoolExecutor(max_workers=max_workers) # create a managed thread pool

    def start(self):
        '''
        Start the Coordinator
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
            if request.get("request_type") == "GET_CLIENT_ID":
                self.handle_get_client_id(client_socket)

            # Handle other request types below
        except json.JSONDecodeError:
            print("Invalid JSON received")

        except Exception as e:
            print(f"Error handling request: {e}")
        
        finally:
            client_socket.close() # use this to close connction once finished 


    def handle_get_client_id(self, client_socket):
        """Generate a new UUID client ID and send it back to client"""
        #ToDo: Cache client and their ID somehow and write it to log

        client_id = str(uuid.uuid4())
        response = {"client_id": client_id}
        client_socket.sendall(json.dumps(response).encode())
        print(f"Generated and sent client ID: {client_id}")

    def check_active_server(self, chunk_server: ChunkServer):
        '''
        makes network call to check if chunk_server is offline
        '''
        # TODO: make network call -> return boolean, true for valid, false for offline
        valid = True # just placeholder for now
        if not valid:
            self.active_chunkservers.remove(chunk_server)
            self.handle_chunk_server_failure()

    def check_active_servers(self):
        '''
        go through self.active_chunkservers to see if any have gone offline unexpectedly
        '''
        for chunk_server in self.active_chunkservers:
            self.check_active_server(chunk_server)

    def handle_chunk_server_failure(self, failed_server: ChunkServer):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        for chunk in failed_server.chunks:
            self.remap_chunk(chunk)

    def handle_add_chunk_server(self, new_server: ChunkServer):
        '''
        handle request for a new ChunkServer to join
        '''
        # TODO: network call to connect chunk server
        pass

    def remove_chunk_server(self, server_to_remove: ChunkServer):
        '''
        handle request for ChunkServer to leave
        '''
        for chunk in server_to_remove.chunks:
            self.remap_chunk(chunk)
        self.active_chunkservers.remove(server_to_remove)

    def handle_new_file(self, new_file: File):
        '''
        handle request when a client stores a new file, call self.map_new_chunk_to_chunk_servers() for each chunk
        '''
        for chunk in new_file:
            self.map_chunk_to_chunk_servers(chunk)

    def get_least_loaded_chunk_servers(self):
        count_to_chunk_server = sorted([(count, chunk_server) for chunk_server, count in self.active_chunkservers])[:max(len(self.active_chunkservers), 3)]
        return count_to_chunk_server

    def map_chunk_to_chunk_servers(self, chunk: Chunk):
        '''
        map each new chunk to 3 chunkservers
        '''
        # have some way of finding the 3 chunkservers that are least loaded at the moment
        chunk_servers = self.get_least_loaded_chunk_servers()
        for chunk_server in chunk_servers:
            # TODO: make calls to chunk_server to add chunk to that chunk_server
            pass

    def remap_chunk(self, chunk: Chunk):
        '''
        remaps chunk to another ChunkServer, called when ChunkServer goes offline
        '''
        self.map_chunk_to_chunk_servers(chunk)

    def handle_delete_file(self, file_id_to_delete: File):
        '''
        removes relevant chunks from ChunkServers when Client deletes a file
        '''
        file = self.file_map[file_id_to_delete]
        for chunk in file.chunks:
            chunk_id = chunk.id
            for chunk_server in self.chunk_map[chunk_id]:
                # TODO: check is chunk_server is alive if so:
                # TODO: send request to chunk_server to delete chunk with chunk_id
                pass