# DFS
Distributed File System (DFS) for video upload, storage and retrival

## File Structure

```sh
distributed-file-system/
├── src/
│   ├── client/        # upload and retrieve files
│   │   └── client.py
│   ├── coordinator/   # manage servers and file replication
│   │   └── coordinator.py
│   ├── chunk_server/  # store and serve chunks
│   │   └── chunk_server.py
│   ├── entry.py       # global entry
│   └── cli.py         # command line interface to run a service
├── README.md
└── requirements.txt
```