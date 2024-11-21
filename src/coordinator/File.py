class File:
    def __init__(self, id):
        self.id = id
        self.chunks = {} # map chunk_index to chunk_id

    def __repr__(self):
        return f'id: {self.id}, chunks: {self.chunks}'
