# src/cli.py
import argparse
# from src.client.client import Client
# from src.coordinator.coordinator import Coordinator
# from src.chunk_server.chunk_server import ChunkServer

def start_service():
    parser = argparse.ArgumentParser(description="Distributed File System CLI")
    parser.add_argument("service", choices=["client", "coordinator", "chunk_server"],
                        help="Specify which service to run.")
    args = parser.parse_args()

    # if args.service == "client":
    #     Client().start()
    # elif args.service == "coordinator":
    #     Coordinator().start()
    # elif args.service == "chunk_server":
    #     ChunkServer().start()
