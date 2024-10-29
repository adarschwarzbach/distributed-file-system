# src/cli.py
import argparse
from src.client.Client import Client
from src.coordinator.Coordinator import Coordinator
from src.chunk_server.ChunkServer import ChunkServer

def start_service():
    parser = argparse.ArgumentParser(description="Distributed File System CLI")
    parser.add_argument("service", choices=["client", "coordinator", "chunk_server"],
                        help="Specify which service to run.")
    parser.add_argument("--host", default="localhost", help="Specify the host address.")
    parser.add_argument("--port", type=int, required=True, help="Specify the port number.")

    args = parser.parse_args()

    if args.service == "client":
        Client(host=args.host, port=args.port).start()
    elif args.service == "coordinator":
        Coordinator(host=args.host, port=args.port).start()
    elif args.service == "chunk_server":
        ChunkServer(host=args.host, port=args.port).start()

