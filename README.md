# wsfs
WebSocket File Server

## Usage
`python3 wsfs.py (path to a file server root)`

## Environment variables
`PORT`: wsfs server port (default: 7772)

## Getting files
Just send a file name or a path to wsfs server and you should start downloading the file

## File download sequence
1. When you send a file name or a path to wsfs server, you will get WSFS_FILE response with the total file size:  
```
WSFS_FILE 65535
           ^--- File size
```

2. After this you will get WSFS_BLOCK response:
```
WSFS_BLOCK 65535 0xABCDEF12
            ^        ^----- CRC32 of the data block
            |--- Block size (the maximum hardcoded size is 128 KB,
                             but it can be lower than 128 KB depending
                             on the total file size)
```

3. After you received WSFS_BLOCK response, the next response should be the actual data

4. After you received the data block, you need to check its CRC32, calculate CRC32 of the block and see if it matches the CRC32 from WSFS_BLOCK response

5. Repeat steps 2, 3 and 4 until you get WSFS_EOF response

Thats it! Simple, isnt it?

## Commands
### ls
Gets human-readable listing of files

### lsr
Gets machine-readable listing of files in JSON

There should be a list of pairs like `["some_file.txt", 65535]`, first entry is the file name, and the second entry is the size, directories have size of -1

### pwd
Gets current directory

### cd
Changes current directory

### disconnect
Disconnects the client from the server
