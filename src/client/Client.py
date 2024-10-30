from typing import *
import time
from pathlib import Path
import json

from src.client.CoordinatorConnection import CoordinatorConnection
from src.client.UploadManager import UploadManager
from src.client.DownloadManager import DownloadManager

class Client:
    def __init__(self, coordinator_host, coordinator_port):
        self.cache_path = Path.home() / '512_dfs_cache'
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.file_metadata = self.load_metadata() # get clients file information


        self.coordinator_connection = CoordinatorConnection(coordinator_host, coordinator_port)
        self.id = self.get_client_id() # get or create client ID

        self.upload_manager = UploadManager(self.coordinator_connection, self.id)
        self.download_manager = DownloadManager(self.coordinator_connection, self.id)


    
    def start(self):
        print("Would you like to (1) upload a file or (2) download a file?")
        choice = input("Enter 1 to upload or 2 to download: ").strip()

        if choice == '1':
            file_location = input("Please enter the file location to upload: ").strip()
            if not Path(file_location).is_file():
                print("The specified file does not exist. Please check the path and try again.")
                return
            
            self.upload_manager.upload_file(file_location, 1, f"{file_location}_{time.time()}")

        elif choice == '2':
            # Prompt for file ID to download
            file_id = input("Please enter the file ID to download: ").strip()
            # Proceed to download
            self.download_manager.download_file(file_id)

        else:
            print("Invalid input. Please enter 1 or 2 to proceed.")
            self.start()  # Retry if input is invalid


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
                print(f"Loaded client id {client_id} from cache")
                return client_id

        else:
            client_id = self.coordinator_connection.get_client_id()
            if client_id is None:
                raise ValueError("Failed to retrieve client ID from Coordinator")
            with open(client_id_file, "w") as file:
                file.write(client_id)
            print(f"Generated and cached new client ID: {client_id}")
            return client_id
    








