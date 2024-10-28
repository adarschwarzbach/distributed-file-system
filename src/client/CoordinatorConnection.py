from typing import *

class CoordinatorConnection:
    '''
        handle connection with coordinator
    '''

    def __init__(self, coord_addr, coord_port):
        self.coord_addr = coord_addr
        self.coord_port = coord_port


    def get_client_id(self):
        # ToDo: request a unique client ID from the server
        pass

    def open_connection(self):
        # ToDo: Open connection
        pass
    
    def close_connection(self):
        # ToDo: Close connection
        pass



