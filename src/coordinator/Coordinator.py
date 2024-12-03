import time
from typing import Dict, Set, List
from src.coordinator.File import File
from src.coordinator.ChunkServerAbstraction import ChunkServerAbstraction
import socket
from concurrent.futures import ThreadPoolExecutor
import uuid 
import json
import collections
import random

class Coordinator:
    def __init__(self, host='localhost', port=6000, max_workers=10):

        # Networking & threading
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5) 
        self.executor = ThreadPoolExecutor(max_workers=max_workers) 

        self.chunk_server_map: Dict[str, ChunkServerAbstraction] = {} #map chunkserver id's to the address and port of the chunkserver
        self.chunk_map: Dict[str, List[str]] = collections.defaultdict(list) #map chunk ids to chunkserver id that hosts it 
        self.file_map: Dict[str, File] = {} #map file_id to File obj
        self.server_chunks_map: Dict[str, Set[str]] = collections.defaultdict(set) #map server id's to the chunks they host


    def start(self):
        self.executor.submit(self.send_heartbeat)
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"connected to {addr}")
            self.executor.submit(self.handle_request, client_socket)



    def handle_request(self, client_socket):
        try:
            data = client_socket.recv(1024).decode().strip()

            if not data:
                print("Received empty request")
                return

            try:
                request = json.loads(data)
                print(f"Received request: {request}")
            except json.JSONDecodeError:
                print("Incomplete or large message detected, switching to buffered reading")
                while True:
                    part = client_socket.recv(1024).decode()
                    if not part:  
                        break
                    data += part
                    if "\n\n" in data:
                        data = data.replace("\n\n", "")  
                        break
                request = json.loads(data)  
                print(f"Buffered request")

            # Dispatch request to the appropriate handler
            if request.get("request_type") == "GET_CLIENT_ID":
                self.handle_get_client_id(client_socket)
            elif request.get("request_type") == "REGISTER_NEW_FILE":
                self.handle_creating_new_file(request)
            elif request.get("request_type") == "REGISTER_CHUNK_SERVER":
                self.handle_new_chunk_server(request)
            elif request.get("request_type") == "GET_CHUNK_SERVERS":
                self.handle_getting_chunk_servers(request, client_socket)
            elif request.get("request_type") == "GET_FILE_DATA":
                self.handle_get_file(request, client_socket)
            elif request.get('request_type') == "CHUNK_UPLOAD_SUCCESS":
                self.handle_chunk_upload_success(request)
            else:
                print(f"Unknown request type: {request.get('request_type')}")

        except json.JSONDecodeError:
            print("Invalid JSON received")

        except Exception as e:
            print(f"Error handling request: {e}")

        finally:
            client_socket.close()  


    def handle_get_file(self, request, client_socket):
        try:
            file_id = request.get('file_id')
            file = self.file_map[file_id]
            chunks = []
            for chunk_id in file.chunks_to_index.keys():
                chunk_servers = []
                for chunk_server_id in self.chunk_map[chunk_id]:
                    chunk_servers.append((json.loads(self.chunk_server_map[chunk_server_id].to_json()))) #appends json location of each chunk_server that holds the chunk
                chunk = {
                    'chunk_id': chunk_id,
                    'chunk_index': file.get_index(chunk_id),
                    'chunk_server_locations': chunk_servers
                }
                chunks.append(chunk)

            response = {
                'file_id': file_id,
                'chunks': chunks
            }

            response_data = json.dumps(response) + '\n\n'
            client_socket.sendall(response_data.encode())
            print(f"Returned file servers to client")
        except Exception as e:
            print(f'Error getting the file data in coordinator: {e}')


    def handle_getting_chunk_servers(self, request, client_socket):
        print("chunk server info requested")
        chunk_servers = []
        for _, chunk_server_abstraction in self.chunk_server_map.items():
            chunk_servers.append(chunk_server_abstraction.to_json())
        response = {
            'chunk_servers': chunk_servers
        }
        response_data = json.dumps(response) + '\n\n'
        client_socket.sendall(response_data.encode())
        print(f"Returned chunk servers to client", response)

        pass

    def handle_creating_new_file(self, request):
        metadata = request.get('chunk_metadata')
        file_name = request.get('file_id')
        new_file = File(file_name)
        self.file_map[file_name] = new_file
        for obj in metadata:
            chunk_id, chunk_index, chunk_server_id = obj['chunk_id'], obj['chunk_index'], obj['chunk_server_id']
            new_file.update_indexes(chunk_id, chunk_index) 

           
    def handle_chunk_upload_success(self, request):
        chunk_id = request.get('chunk_id')
        chunk_server_id = request.get('chunk_server_id')
        self.chunk_map[chunk_id].append(chunk_server_id)
        self.server_chunks_map[chunk_server_id].add(chunk_id)
       

    def handle_get_client_id(self, client_socket):
        """Generate a new UUID client ID and send it back to client"""
        client_id = str(uuid.uuid4())
        response = {"client_id": client_id}
        client_socket.sendall(json.dumps(response).encode())
        print(f"Generated and sent client ID: {client_id}")


    def send_heartbeat(self):
        while True:
            chunk_server_ids = list(self.chunk_server_map.keys())
            print('\nHeartbeat sent')
            for server_id in chunk_server_ids:
                other_servers = [id_ for id_ in chunk_server_ids if id_ != server_id]
                if len(other_servers) >= 2:
                    assigned_servers_ids = random.sample(other_servers, 2)
                else:
                    assigned_servers_ids = other_servers  # Use whatever is available

                assigned_servers = [self.chunk_server_map[assigned_server].get_location() for assigned_server in assigned_servers_ids]
                request = {
                    'request_type': 'HEALTH_CHECK',
                    'other_active_servers': assigned_servers
                }
                try:
                    chunk_server_addr, chunk_server_port = self.chunk_server_map[server_id].get_location()
                    chunk_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    chunk_server_socket.connect((chunk_server_addr, chunk_server_port))
                    chunk_server_socket.send((json.dumps(request) + '\n\n').encode())

                    data = ""
                    while True:
                        part = chunk_server_socket.recv(1024).decode()
                        if not part:  # Connection closed
                            break
                        data += part
                        if "\n\n" in data:  # End of message
                            data = data.replace("\n\n", "")  # Remove delimiter
                            break

                    response = json.loads(data)

                    if response.get('status') != 'OK':
                        self.handle_chunk_server_failure(server_id)

                except Exception as e:
                    print(f'A heartbeat has failed for server {server_id}: {e}')
                    self.handle_chunk_server_failure(server_id)
                finally:
                    chunk_server_socket.close()

            time.sleep(10)

    def handle_new_chunk_server(self, request):
        id = request.get('chunk_server_id')
        address = request.get('host')
        port = request.get('port')
        self.chunk_server_map[id] = ChunkServerAbstraction(address, port, id)
        print(self.chunk_server_map, "CHUNK SERVER MAP")
        pass

    def handle_chunk_server_failure(self, failed_server):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        print(f"Handling failure of chunk server {failed_server}")
        chunks_to_remap = list(self.server_chunks_map[failed_server])

        for chunk_id in chunks_to_remap:
            self.chunk_map[chunk_id].remove(failed_server)
        
        del self.server_chunks_map[failed_server]
        del self.chunk_server_map[failed_server]

        print(chunks_to_remap, 'CHUNKS TO REMAP')
        
        # Remap each chunk to a new server
        for chunk_id in chunks_to_remap:
            self.remap_chunk(chunk_id)
        pass

    # def remove_chunk_server(self, server_to_remove):
    #     '''
    #     handle request for ChunkServer to leave
    #     '''
    #     pass
    

    def remap_chunk(self, chunk_id):
        '''
        remaps chunk to another ChunkServer, called when ChunkServer goes offline
        '''
        try:
            available_servers = [server_id for server_id in self.chunk_server_map if server_id not in self.chunk_map[chunk_id]]
            print(available_servers, 'AVAILABLE SERVER(S)')
            if not available_servers:
                print(f"No available servers to replicate chunk {chunk_id}")
                return

            # Select a random server to host the chunk
            target_server_id = available_servers[0]
            source_server_id = self.chunk_map[chunk_id][0]  # Assume at least one server hosts the chunk

            source_server = self.chunk_server_map[source_server_id]
            target_server = self.chunk_server_map[target_server_id]

            target_address, target_port = target_server.get_location()
            source_address, source_port = source_server.get_location()
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as source_socket:
                source_socket.connect((source_address, source_port))
                request = {
                    "request_type": "REPLICATE_CHUNK",
                    "chunk_id": chunk_id,
                    "chnk_srv_addr": target_address,
                    "chnk_srv_port": target_port
                }
                source_socket.sendall((json.dumps(request) + '\n\n').encode())
                print(f"Replication request sent for chunk {chunk_id} from {source_server_id} to {target_server_id}")

                data = ""
                while True:
                    part = source_socket.recv(1024).decode()
                    if not part or "\n\n" in part:
                        break
                    data += part
            
            if data:
                response = json.loads(data)
                if response.get("status") == "success":
                    # Only update chunk_map after confirmed success
                    self.chunk_map[chunk_id].append(target_server_id)
                    print(f"Successfully remapped chunk {chunk_id} to server {target_server_id}")
                else:
                    print(f"Failed to remap chunk {chunk_id}: {response.get('error')}")

        except Exception as e:
            print(f"Error remapping chunk {chunk_id}: {e}")
