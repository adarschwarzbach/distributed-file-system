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
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM)  as s:
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
