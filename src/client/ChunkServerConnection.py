from typing import *

class ChunkServerConnection:
    def __init__(self, chnk_srv_addr, chnk_srv_port):
        self.chnk_srv_addr = chnk_srv_addr
        self.chnk_srv_port = chnk_srv_port
        

    def upload_chunk(self, chunk_object):
        #ToDo: upload a given chunk to a given chunk server
        pass

    
    def download_chunk(self, chunk_id):
        #ToDo: Download a given chunk from a given chunk server
        pass
