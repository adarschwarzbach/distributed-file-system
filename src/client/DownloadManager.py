from typing import *
import os
from pathlib import Path
import json


class DownloadManager:
    '''
        Handle downloading, reassembling and writing files
    '''

    def __init__(self, file_id):
        self.file_id = file_id
    
    def download_chunks(self):
        # ToDo: download chunks in parallel 
        pass

    
    def assemble_file(self):
        # 
        pass
