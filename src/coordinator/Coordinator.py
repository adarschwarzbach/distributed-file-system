from typing import Dict, Set, List
from src.coordinator.File import File
from src.chunk_server.ChunkServer import ChunkServer
from src.chunk_server.Chunk import Chunk
import socket
from concurrent.futures import ThreadPoolExecutor
import uuid 
import json


class Coordinator:
    def __init__(self, host='localhost', port=6000, max_workers=10):
        # maps file_id to a File object
        self.file_map: Dict[int, File] = {}
        # maps chunk_id to the 3 ChunkServers where we can find that chunk
        self.chunk_map: Dict[int, List[ChunkServer]] = {}
        # dict of ChunkServers that are online mapping to the number of chunks on that chunk server
        self.active_chunkservers: Dict[ChunkServer, int] = {}

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
            elif request.get("request_type") == "ADD_CHUNK_SERVER":
                self.handle_add_chunk_server(request.get("chunk_server"))
            elif request.get("request_type") == "GET_CHUNK_LOCATIONS":
                self.handle_get_chunk_locations
            elif request.get("request_type") == "NEW_FILE":
                new_file = request.get("file")
                self.handle_new_file(File(**new_file))
            elif request.get("request_type") == "DELETE_FILE":
                file_id = request.get("file_id")
                self.handle_delete_file(file_id)
            else:
                print("Unknown request type")
            
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
    
    def handle_get_chunk_locations(self, client_socket, request):
        file_id = request.get('file_id')
        if file_id in self.file_map:
            file = self.file_map[file_id]
            chunk_locations = {chunk.id: [server.id for server in self.chunk_map.get(chunk.id, [])] for chunk in file.chunks}
            response = {"status": "success", "chunk_locations": chunk_locations}
        else:
            response = {"status": "error", "message": "File ID not found"}
        
        client_socket.sendall(json.dumps(response).encode())
        self.log_info(f"Sent chunk locations for file ID {file_id}")

    def check_active_server(self, chunk_server: ChunkServer):
        '''
        makes network call to check if chunk_server is offline
        '''
        try: 
            with socket.create_connection((chunk_server.host, chunk_server.port), timeout=5) as conn:
                health_check_request = json.dumps({"request_type": "HEALTH_CHECK"})
                conn.sendall(health_check_request.encode())
                response = conn.recv(1024).decode()
                response_data = json.loads(response)
                return response_data.get("status") == "OK"

        except Exception as e:
            print(f'Health check for chunkserver failed: {e}')
            return False

    def check_active_servers(self):
        '''
        go through self.active_chunkservers to see if any have gone offline unexpectedly
        '''
        offline_servers = []
        for chunk_server in list(self.active_chunkservers):
            if not self.check_active_server(chunk_server):
                offline_servers.append(chunk_server)
        for server in offline_servers:
            self.handle_chunk_server_failure(server)

    def handle_chunk_server_failure(self, failed_server: ChunkServer):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        for chunk in failed_server.chunks:
            self.remap_chunk(chunk)
        del self.active_chunkservers[failed_server]

    def handle_add_chunk_server(self, new_server: ChunkServer):
        '''
        handle request for a new ChunkServer to join
        '''
        # TODO: network call to connect chunk server
        # !!!!!!
        self.active_chunkservers[new_server] = 0
        pass

    def remove_chunk_server(self, server_to_remove: ChunkServer):
        '''
        handle request for ChunkServer to leave
        '''
        for chunk in server_to_remove.chunks:
            self.remap_chunk(chunk)
        del self.active_chunkservers[server_to_remove]
        print(f"Removed chunk server: {server_to_remove}")

    def handle_new_file(self, new_file: File):
        '''
        handle request when a client stores a new file, call self.map_new_chunk_to_chunk_servers() for each chunk
        '''
        for chunk in new_file:
            self.map_chunk_to_chunk_servers(chunk)
        self.file_map[new_file.id] = new_file
        print(f"New file handled: {new_file.id}")

    def get_least_loaded_chunk_servers(self) -> List[ChunkServer]:
        sorted_servers = sorted(self.active_chunkservers.items(), key=lambda x: x[1])
        return [server for _, server in sorted_servers[:3]]

    def map_chunk_to_chunk_servers(self, chunk: Chunk):
        '''
        map each new chunk to 3 chunkservers
        '''
        chunk_servers = self.get_least_loaded_chunk_servers()
        self.chunk_map[chunk.id] = chunk_servers
        for chunk_server in chunk_servers:
            chunk_server.upload_chunk(chunk)
            self.active_chunkservers[chunk_server] += 1
        print(f"Chunk {chunk.id} mapped to servers: {chunk_servers}")

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
            for chunk_id in self.chunk_map:
                for chunk_server in self.chunk_map[chunk_id]:
                    if self.check_active_server(chunk_server):
                        chunk_server.delete_chunk(chunk_id)
                        self.active_chunkservers[chunk_server] -= 1
        del self.file_map[file_id_to_delete]