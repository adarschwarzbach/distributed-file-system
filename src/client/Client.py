from typing import *
import os
from pathlib import Path


class Client:

    def __init__(self):
        self.cache_path = Path.home() / './512_dfs_cache'
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        

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
        pass







