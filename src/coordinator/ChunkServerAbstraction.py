import json

class ChunkServerAbstraction:
    def __init__(self, address, port, id):
        self.chnk_srv_addr = address
        self.chnk_srv_port = port
        self.chnk_srv_id = id

    def __repr__(self):
        return f'address: {self.chnk_srv_addr}, port: {self.chnk_srv_port}, id: {self.chnk_srv_id}'
    

    def to_json(self):
        return json.dumps({'chnk_srv_addr': self.chnk_srv_addr, 
                            'chnk_srv_port': self.chnk_srv_port,
                            'chnk_srv_id': self.chnk_srv_id})
    