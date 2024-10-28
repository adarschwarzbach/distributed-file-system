from typing import *
import os
from pathlib import Path
import json

from CoordinatorConnection import CoordinatorConnection

class Client:

    def __init__(self):
        self.cache_path = Path.home() / './512_dfs_cache'
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_metadata = self.load_metadata() # get clients file information
        self.id = self.get_client_id() # get or create client ID

    
    def start(self):
        # ToDo: Main loop to upload and download files until end
        pass

    def load_metadata(self):
        # Load cached metadata on file/chunk locations
        metadata_file = self.cache_path / 'uploaded_file_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as file:
                return json.load(file)
        else:
            return None


    def get_client_id(self) -> None:
        client_id_file = self.cache_path / 'client_id.txt'

        if client_id_file.exists():
            with open(client_id_file, 'r') as file:
                client_id = file.read().strip()
                self.client_id = client_id

        else:
            self.client_id = self.generate_client_id()
    

    def generate_client_id(self) -> str:
        '''
            ToDo: Request new client ID from coordinator
        '''
        client_connection = CoordinatorConnection()
        id = client_connection.get_client_id()
        client_connection.close_connection()

        return id








