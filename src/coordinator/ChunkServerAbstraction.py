class ChunkServerAbstraction:
    def __init__(self, address, port, id):
        self.chnk_srv_addr = address
        self.chnk_srv_port = port
        self.chnk_srv_id = id