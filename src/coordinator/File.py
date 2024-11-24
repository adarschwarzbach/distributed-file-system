class File:
    #maintain the file id and the indexes of the chunks
    def __init__(self, id):
        self.id = id
        self.chunks_to_index = {} # map chunk_ids to the chunk_index

    def update_indexes(self, chunk_id, chunk_index):
        self.chunks_to_index[chunk_id] = chunk_index

    def get_index(self, chunk_id):
        if chunk_id not in self.chunks_to_index:
            raise Exception('Chunk ID not in Files Chunk Map')

        return self.chunks_to_index[chunk_id]

    def __repr__(self):
        return f'id: {self.id}, chunks: {self.chunks}'
