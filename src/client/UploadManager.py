from typing import *
import uuid

class UploadManager:
    '''
        Read, chunk and upload files
    ''' 
    
    def __init__(self, file_location):
        self.file_location = file_location

    def chunk_file(self, chunk_size_mb, file_id):
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        chunks = []

        chunk_index = 0

        with open(self.file_location, 'rb') as file:
            while True:
                chunk = file.read(chunk_size_bytes)
                if not chunk:
                    break

                chunks.append({
                                'chunk_index': chunk_index,
                                'chunk_id': f"{uuid.uuidr()}",
                                'chunk': chunk
                            })
                chunk_index += 1


        self.upload_file(chunks, file_id)


    def upload_file(self, file_chunks, file_id):
        '''
            Upload file in parallel
        '''
        pass

        

        



    




