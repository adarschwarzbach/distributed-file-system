from typing import Dict, Set, List
from src.coordinator.File import File
from src.coordinator.ChunkServer import ChunkServer
from src.coordinator.Chunk import Chunk
import socket
from concurrent.futures import ThreadPoolExecutor
import uuid 


class Coordinator:
    def __init__(self, host='localhost', port=6000, max_workers=10):
        # maps file_id to a File object
        file_map: Dict[int, File] = {}
        # maps chunk_id to the 3 ChunkServers where we can find that chunk
        chunk_map: Dict[int, List[ChunkServer]] = {}
        # set of ChunkServers that are online
        active_chunkservers: Set[ChunkServer] = set()

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
            request = client_socket.recv(1024).decode()
            print(f"Recieved request: {request}")
            if request == "GET_CLIENT_ID":
                self.handle_get_client_id(client_socket)

        except Exception as e:
            print(f"Error handling request: {e}")
        
        finally:
            client_socket.close() # use this to close connction once finished 


    def handle_get_client_id(self, client_socket):
        """Generate a new UUID client ID and send it back to client"""
        #ToDo: Cache client and their ID somehow and write it to log

        client_id = str(uuid.uuid4())
        client_socket.send(client_id.encode())
        print(f"Generated and sent client ID: {client_id}")


    def check_active_servers(self):
        '''
        go through self.active_chunkservers to see if any have gone offline unexpectedly
        '''
        pass

    def handle_chunk_server_failure(self, failed_server: ChunkServer):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        pass

    def add_chunk_server(self, new_server: ChunkServer):
        '''
        handle request for a new ChunkServer to join
        '''
        pass

    def remove_chunk_server(self, server_to_remove: ChunkServer):
        '''
        handle request for ChunkServer to leave
        '''
        pass

    def handle_new_file(self, new_file: File):
        '''
        handle request when a client stores a new file, call self.map_new_chunk_to_chunk_servers() for each chunk
        '''

    def map_chunk_to_chunk_servers(self, chunk: Chunk):
        '''
        map each new chunk to 3 chunkservers
        '''
        pass

    def remap_chunk(self, chunk: Chunk):
        '''
        remaps chunk to another ChunkServer, called when ChunkServer goes offline
        '''

    def handle_delete_file(self, file_to_delete: File):
        '''
        removes relevant chunks from ChunkServers when Client deletes a file
        '''