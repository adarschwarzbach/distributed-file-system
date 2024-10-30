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


# API Documentation

## Overview
This document specifies the API structure and return object for the `Coordinator` server and `Chunk Server` based on the `Client`, `UploadManager`, and `DownloadManager` classes. 

---

## 1. Coordinator Server API

### 1.1 `GET_CLIENT_ID`
- **Description**: Requests a unique client ID.
- **Request Format**:
    ```json
    {
      "request_type": "GET_CLIENT_ID"
    }
    ```
- **Response Format**:
    ```json
    {
      "client_id": "<unique_client_id>"
    }
    ```
- **Error Handling**: Returns `null` for `client_id` if unable to generate a client ID.

---

### 1.2 `GET_CHUNK_SERVERS`
- **Description**: Requests a list of available chunk servers for uploading files.
- **Request Format**:
    ```json
    {
      "request_type": "GET_CHUNK_SERVERS"
    }
    ```
- **Response Format**:
    ```json
    {
      "chunk_servers": [
        {
          "chnk_srv_addr": "<server_address>",
          "chnk_srv_port": "<server_port>",
          "chnk_srv_id": "<unique_chunk_server_id>"
        },
        ...
      ]
    }
    ```
- **Error Handling**: If no chunk servers are available, respond with `"chunk_servers": []`.

---

### 1.3 `GET_CHUNK_LOCATIONS`
- **Description**: Requests the locations of chunks for a specific file, including replicas.
- **Request Format**:
    ```json
    {
      "request_type": "GET_CHUNK_LOCATIONS",
      "file_id": "<file_id>"
    }
    ```
- **Response Format**:
    ```json
    {
      "chunk_locations": {
        "<chunk_id>": [
          {
            "chnk_srv_addr": "<server_address>",
            "chnk_srv_port": "<server_port>",
            "chnk_srv_id": "<unique_chunk_server_id>"
          },
          { "replica_2" }, 
          { "replica_3" }
        ],
        ...
      }
    }
    ```
- **Error Handling**: If no locations are found, return an empty dictionary: `"chunk_locations": {}`.

---

## 2. Chunk Server API

### 2.1 `UPLOAD_CHUNK`
- **Description**: Handles uploading a single chunk of a file.
- **Request Format**:
    ```json
    {
      "request_type": "UPLOAD_CHUNK",
      "chunk_id": "<chunk_id>",
      "chunk_index": <integer_index>,
      "chunk_size": <size_in_bytes>,
      "user_id": "<client_user_id>"
    }
    ```
    - After this JSON object, the chunk binary data should follow with a delimiter `"\n\n"`.
- **Response Format**:
    ```json
    {
      "status": "success"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Error message describing failure reason"
    }
    ```
- **Error Handling**: If uploading fails, the server should retry up to `max_retries`. Each failure should include a message indicating the failure reason.

---

### 2.2 `DOWNLOAD_CHUNK`
- **Description**: Downloads a specific chunk from the server.
- **Request Format**:
    ```json
    {
      "request_type": "DOWNLOAD_CHUNK",
      "chunk_id": "<chunk_id>"
    }
    ```
- **Response Format**:
    ```json
    {
      "status": "success",
      "chunk_index": <integer_index>,
      "chunk_data": "<base64_encoded_chunk_data>"
    }
    ```
    - Note: `chunk_data` should be returned as binary data following a JSON object.
  
    or in case of an error:
    ```json
    {
      "status": "error",
      "message": "Error message describing failure reason"
    }
    ```
- **Error Handling**: If downloading fails for any reason, return an error message with details.

---

## 3. Client File Metadata Format

### Metadata Cache File (`<file_id>_metadata.json`)
- **Description**: Stores metadata for uploaded files, listing each chunk ID and its respective index.
- **Format**:
    ```json
    [
      {
        "chunk_id": "<chunk_id>",
        "chunk_index": <integer_index>
      },
      ...
    ]
    ```

---

## Example Interaction Flow

### Upload Flow
1. The client requests `GET_CLIENT_ID` from the Coordinator to obtain a unique ID.
2. The client requests `GET_CHUNK_SERVERS` to retrieve available servers for uploading.
3. The client chunks a file and uploads each chunk to a chunk server using `UPLOAD_CHUNK`.
4. Each successful upload logs metadata locally in `<file_id>_metadata.json`.

### Download Flow
1. The client retrieves `GET_CHUNK_LOCATIONS` to determine where each chunk of the requested file is located.
2. The client iterates through each chunk's servers and initiates `DOWNLOAD_CHUNK` requests.
3. Upon successful download of all chunks, the client reassembles the file based on `chunk_index`.
