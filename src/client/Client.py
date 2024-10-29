from typing import *
import os
from pathlib import Path
import json

from src.client.CoordinatorConnection import CoordinatorConnection

class Client:
    def __init__(self, coordinator_host, coordinator_port):
        self.cache_path = Path.home() / '512_dfs_cache'
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.file_metadata = self.load_metadata() # get clients file information


        self.coordinator_connection = CoordinatorConnection(coordinator_host, coordinator_port)
        self.id = self.get_client_id() # get or create client ID


    
    def start(self):
        # ToDo: Main loop to upload and download files until end
        pass


    def load_metadata(self) -> Optional[dict]:
        # Load cached metadata on file/chunk locations
        metadata_file = self.cache_path / 'uploaded_file_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as file:
                return json.load(file)
        else:
            return {}


    def get_client_id(self) -> str:
        client_id_file = self.cache_path / 'client_id.txt'

        if client_id_file.exists():
            with open(client_id_file, 'r') as file:
                client_id = file.read().strip()
                print(f"Loaded client id from cache")
                return client_id

        else:
            client_id = self.coordinator_connection.get_client_id()
            if client_id is None:
                raise ValueError("Failed to retrieve client ID from Coordinator")
            with open(client_id_file, "w") as file:
                file.write(client_id)
            print(f"Generated and cached new client ID: {client_id}")
            return client_id
    








