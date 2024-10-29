from typing import Dict, Set, List
from coordinator.File import File
from coordinator.ChunkServer import ChunkServer
from coordinator.Chunk import Chunk

class Coordinator:
    def __init__(self):
        # maps file_id to a File object
        file_map: Dict[int, File] = {}
        # maps chunk_id to the 3 ChunkServers where we can find that chunk
        chunk_map: Dict[int, List[ChunkServer]] = {}
        # set of ChunkServers that are online
        active_chunkservers: Set[ChunkServer] = set()

    def start(self):
        '''
        Start the Coordinator
        '''

    def check_active_servers(self):
        '''
        go through self.active_chunkservers to see if any have gone offline unexpectedly
        '''
        pass

    def handle_chunk_server_failure(self, failed_server: ChunkServer):
        '''
        if a ChunkServer goes offline unexpectedly, map all the chunks it stored to another ChunkServer,
        call self.remap_chunk()
        '''
        pass

    def add_chunk_server(self, new_server: ChunkServer):
        '''
        handle request for a new ChunkServer to join
        '''
        pass

    def remove_chunk_server(self, server_to_remove: ChunkServer):
        '''
        handle request for ChunkServer to leave
        '''
        pass

    def handle_new_file(self, new_file: File):
        '''
        handle request when a client stores a new file, call self.map_new_chunk_to_chunk_servers() for each chunk
        '''

    def map_chunk_to_chunk_servers(self, chunk: Chunk):
        '''
        map each new chunk to 3 chunkservers
        '''
        pass

    def remap_chunk(self, chunk: Chunk):
        '''
        remaps chunk to another ChunkServer, called when ChunkServer goes offline
        '''

    def handle_delete_file(self, file_to_delete: File):
        '''
        removes relevant chunks from ChunkServers when Client deletes a file
        '''