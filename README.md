# DFS
Distributed file system for video upload, storage and retrival

## File Structure

```sh
distributed-file-system/
├── src/
│   ├── __init__.py
│   ├── client/        # upload and retrieve files
│   │   ├── __init__.py
│   │   └── client.py
│   ├── coordinator/   # manage servers and file replication
│   │   ├── __init__.py
│   │   └── coordinator.py
│   ├── chunk_server/  # store and serve chunks
│   │   ├── __init__.py
│   │   └── chunk_server.py
│   ├── entry.py       # global entry
│   └── cli.py         # command line interface to run a service
├── README.md
└── requirements.txt
```