from typing import Dict, Set, List
from src.coordinator.File import File
from src.coordinator.ChunkServerAbstraction import ChunkServerAbstraction
import socket
from concurrent.futures import ThreadPoolExecutor
import uuid 
import json
import collections

class Coordinator:
    def __init__(self, host='localhost', port=6000, max_workers=10):

        ###   I THINK THIS COMMENTED STUFF IS ALL GARBAGE BELOW
        # maps file_id to a File object
        #self.file_map: Dict[int, File] = {}
        # maps chunk_id to the 3 ChunkServers where we can find that chunk
        #self.chunk_map: Dict[int, List[ChunkServer]] = {}
        # set of ChunkServers that are online
        #self.active_chunkservers: Set[ChunkServer] = set()

        # Networking & threading
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 over TCP
        self.server_socket.bind((self.host, self.port)) # Tells OS port is taken for incoming connections
        self.server_socket.listen(5) # Up to 5 concurrent connections, after 5, requests are queued
        self.executor = ThreadPoolExecutor(max_workers=max_workers) # create a managed thread pool

        #ben's code
        self.chunk_server_map: Dict[int, ChunkServerAbstraction] = {} #map chunkserver id's to the address and port of the chunkserver
        self.chunk_map: Dict[int, List[int]] = collections.defaultdict(list) #map chunk ids to chunkserver id that hosts it --> WILL NEED TO CHANGE WHEN WE ADD REPLICATION BUT GOOD STARTING POINT
        self.file_map: Dict[int, File] = {}

        self.file_to_chunk_to_server = {} # {file_id: [{chunk_id, chunk_index, [chunk_server(s)]}]}

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
            # Attempt to read a single message (small messages)
            data = client_socket.recv(1024).decode().strip()

            # If data is empty, handle gracefully
            if not data:
                print("Received empty request")
                return

            try:
                # Try parsing the single message as JSON
                request = json.loads(data)
                print(f"Received request: {request}")
            except json.JSONDecodeError:
                # Fallback to buffered reading if JSON parsing fails
                print("Incomplete or large message detected, switching to buffered reading")
                while True:
                    part = client_socket.recv(1024).decode()
                    if not part:  # Client closed connection
                        break
                    data += part
                    if "\n\n" in data:
                        data = data.replace("\n\n", "")  # Remove delimiter
                        break
                request = json.loads(data)  # Parse the complete buffered message
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
                self.handle_get_file(client_socket)
            else:
                print(f"Unknown request type: {request.get('request_type')}")

        except json.JSONDecodeError:
            print("Invalid JSON received")

        except Exception as e:
            print(f"Error handling request: {e}")

        finally:
            client_socket.close()  # Ensure the connection is closed


    def handle_get_file(self, client_socket):
        response_data = json.dumps(self.file_to_chunk_to_server) + '\n\n'
        client_socket.sendall(response_data.encode())
        print(f"Returned file servers to client")


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
        # print('ran handle_creating_new_file')
        self.file_to_chunk_to_server[file_name] = []
        new_file = File(file_name)
        chunk_indexes_to_ids = {}
        for obj in metadata:
            chunk_id, chunk_index, chunk_server_id = obj['chunk_id'], obj['chunk_index'], obj['chunk_server_id']
            self.chunk_map[chunk_id].append(chunk_server_id)
            chunk_indexes_to_ids[chunk_index] = chunk_id

            self.file_to_chunk_to_server[file_name].append({"chunk_id":chunk_id, "chunk_index":chunk_index, "server_info":self.chunk_server_map[chunk_server_id].to_json()})

        print('\n\n\n')
       


        new_file.chunks = chunk_indexes_to_ids
        self.file_map[file_name] = new_file
        # print(self.file_map)
        # print(self.chunk_map)

        # file_id = request.get('file_id')
        # chunk_metadata = request.get('chunk_metadata')
        # chunk_ids = [chunk["chunk_id"] for chunk in chunk_metadata]

        # #store file
        # file = File(file_id, chunk_ids)
        # self.file_map[file_id] = file

        # #store where each chunk can be found
        # for chunk in chunk_metadata:
        #     chunk_id, chunk_server_id = chunk['chunk_id'], chunk['chunk_server_id']
        #     self.chunk_map[chunk_id] = chunk_server_id




    def handle_get_client_id(self, client_socket):
        """Generate a new UUID client ID and send it back to client"""
        #ToDo: Cache client and their ID somehow and write it to log

        client_id = str(uuid.uuid4())
        response = {"client_id": client_id}
        client_socket.sendall(json.dumps(response).encode())
        print(f"Generated and sent client ID: {client_id}")


    def check_active_servers(self):
        '''
        go through self.active_chunkservers to see if any have gone offline unexpectedly
        '''
        pass

    def handle_chunk_server_failure(self, failed_server):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        pass

    def handle_new_chunk_server(self, request):
        id = request.get('chunk_server_id')
        address = request.get('host')
        port = request.get('port')
        self.chunk_server_map[id] = ChunkServerAbstraction(address, port, id)
        print(self.chunk_server_map, "CHUNK SERVER MAP")
        pass


    def remove_chunk_server(self, server_to_remove):
        '''
        handle request for ChunkServer to leave
        '''
        pass
    

    def map_chunk_to_chunk_servers(self, chunk):
        '''
        map each new chunk to 3 chunkservers
        '''
        pass

    def remap_chunk(self, chunk):
        '''
        remaps chunk to another ChunkServer, called when ChunkServer goes offline
        '''

    # def handle_delete_file(self, file_to_delete: File):
    #     '''
    #     removes relevant chunks from ChunkServers when Client deletes a file
    #     '''