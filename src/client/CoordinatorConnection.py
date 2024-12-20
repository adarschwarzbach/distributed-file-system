from typing import *
import socket
import json

class CoordinatorConnection:
    # handle connection with coordinator
    def __init__(self, coord_addr, coord_port):
        self.coord_addr = coord_addr
        self.coord_port = coord_port


    def get_client_id(self) -> Optional[int]:
        # Request a unique client ID from the server
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.coord_addr, self.coord_port))

                request = {"request_type": "GET_CLIENT_ID"}
                s.sendall(json.dumps(request).encode())
                print("Client ID request sent to Coordinator server")

                data = s.recv(1024).decode()
                response = json.loads(data)  # Parse JSON response
                client_id = response.get("client_id")
                print(f"Received ID {client_id} from Coordinator server")
                return client_id
            
        except Exception as e:
            print(f"Error getting client ID: {e}")
            return None
        
    def get_chunk_servers(self):
        """Get a list of Chunk Servers to upload to"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.coord_addr, self.coord_port))
                request = {"request_type": "GET_CHUNK_SERVERS"}
                s.sendall(json.dumps(request).encode())
                print("Requested Chunk Server locations from Coordinator")

                # Collect response data until we reach the end of the message
                data = ""
                while True:
                    part = s.recv(1024).decode()
                    if not part:
                        break
                    data += part
                    if "\n\n" in data:
                        data = data.replace("\n\n", "")
                        break

                response = json.loads(data)
                chunk_servers = response.get("chunk_servers", [])  # form [{chnk_srv_addr, chnk_srv_port, chnk_srv_id}, ...]
                chunk_servers = [json.loads(server) for server in chunk_servers]
                
                if not chunk_servers:
                    print("No Chunk Servers available from Coordinator.")
                
                return chunk_servers

        except Exception as e:
            print(f"Error getting Chunk Servers: {e}")
            return []
    

    def get_chunk_locations(self, file_id):
        """Get the raw JSON object of Chunk Servers holding pieces of the file"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.coord_addr, self.coord_port))
                request = {"request_type": "GET_FILE_DATA", "file_id": file_id}
                s.sendall((json.dumps(request) + "\n\n").encode())  # Add delimiter
                print("Requested Chunk locations from Coordinator")
                print("Request:", request)

                # Buffer to collect response data
                data = ""
                while True:
                    part = s.recv(1024).decode()
                    if not part:  # Connection closed
                        break
                    data += part
                    if "\n\n" in data:  # End of message
                        data = data.replace("\n\n", "")  # Remove delimiter
                        break

                response = json.loads(data)  # Parse the raw JSON response
                print("Raw Response:", response)

                return response  # Return the raw JSON object directly

        except Exception as e:
            print(f"Error getting chunk locations: {e}")
            return None


    def register_new_file(self, file_id, chunk_metadata):
        req = {
            'request_type': 'REGISTER_NEW_FILE',
            'file_id': file_id,
            'chunk_metadata': chunk_metadata
        }
        try:
            serialized_req = json.dumps(req)  # Serialize request to check for issues
            print(f"Serialized Request: {serialized_req}")  # Debug log
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.coord_addr, self.coord_port))
                s.sendall(serialized_req.encode())  # Send JSON to the server

        except Exception as e:
            print(f'Error registering new file: {e}')
        
