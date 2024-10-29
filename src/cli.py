# src/cli.py
import argparse
from src.client.Client import Client
from src.coordinator.Coordinator import Coordinator
from src.chunk_server.ChunkServer import ChunkServer

def start_service():
    parser = argparse.ArgumentParser(description="Distributed File System CLI")
    parser.add_argument("service", choices=["client", "coordinator", "chunk_server"],
                        help="Specify which service to run.")
    
    # Optional arguments for the client
    parser.add_argument("--coordinator_host", default="localhost",
                        help="Specify the coordinator's host address (only for client).")
    parser.add_argument("--coordinator_port", type=int, default=5000,
                        help="Specify the coordinator's port number (only for client).")
    
    # Host and port for the coordinator and chunk server
    parser.add_argument("--host", default="localhost", help="Specify the host address.")
    parser.add_argument("--port", type=int, help="Specify the port number (required for coordinator and chunk_server).")
    parser.add_argument("--max_workers", type=int, default=10,
                        help="Specify the maximum number of worker threads (only for coordinator and chunk_server).")

    args = parser.parse_args()

    # Check required arguments based on service type
    if args.service == "client":
        # Initialize Client and pass coordinator's host and port
        Client(coordinator_host=args.coordinator_host, coordinator_port=args.coordinator_port).start()
    elif args.service == "coordinator":
        # Ensure --port is specified for the coordinator
        if args.port is None:
            parser.error("--port is required for the coordinator")
        Coordinator(host=args.host, port=args.port, max_workers=args.max_workers).start()
    elif args.service == "chunk_server":
        # Ensure --port is specified for the chunk server
        if args.port is None:
            parser.error("--port is required for the chunk_server")
        ChunkServer(host=args.host, port=args.port, max_workers=args.max_workers).start()

if __name__ == "__main__":
    start_service()
