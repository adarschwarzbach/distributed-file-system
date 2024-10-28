from typing import *

class UploadManager:
    '''
        Read, chunk and upload files
    ''' 
    
    def __init__(self, file_location):
        self.file_location = file_location

    def chunk_file(self, chunk_size_mb):
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.chunks = []

        chunk_index = 0

        with open(self.file_location, 'rb') as file:
            while True:
                chunk = file.read(chunk_size_bytes)
                if not chunk:
                    break

                self.chunks.append({
                                'chunk_index': chunk_index,
                                'chunk': chunk
                            })
                chunk_index += 1

        



    




