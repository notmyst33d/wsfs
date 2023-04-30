import os, asyncio, zlib, sys, time, humanize
from aiohttp import ClientSession, WSMsgType

async def client_get(response, path):
    await response.send_str(path)

    msg = await response.receive()
    if not msg.data.startswith("WSFS_FILE"):
        print("File not found")
        return

    file = open(path.split("/")[-1], "wb")
    file_size = msg.data.split(" ")[1]
    bytes_received = 0
    print(f"Received a file with a size of {humanize.naturalsize(file_size, format='%.2f')}")

    stime = time.time()
    while True:
        sys.stdout.write("\r")
        sys.stdout.flush()

        msg = await response.receive()
        if msg.type == WSMsgType.TEXT:
            if msg.data == "WSFS_EOF":
                break

        block_data = msg.data.split(" ")

        msg = await response.receive()
        if hex(zlib.crc32(msg.data)) != block_data[2]:
            print("CRC32 error")
            return False

        file.write(msg.data)
        bytes_received += int(block_data[1])

        sys.stdout.write(f"\x1b[2KDownloading {path} [{humanize.naturalsize(bytes_received, format='%.2f')} / {humanize.naturalsize(file_size, format='%.2f')}]")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    print(f"Took {round(time.time() - stime, 1)} seconds to receive {humanize.naturalsize(file_size, format='%.2f')}")

    await response.send_str("disconnect")
    file.close()

    return True

async def client_put(response, path, destination):
    await response.send_str(f"put {destination}")

    msg = await response.receive()
    if msg.data != "WSFS_OK":
        print(f"Server: {msg.data}")
        return False

    file = open(path, "rb")
    file_size = os.path.getsize(path)
    bytes_sent = 0

    print(f"Uploading a file with a size of {humanize.naturalsize(file_size, format='%.2f')}")
    await response.send_str(f"WSFS_FILE {file_size}")

    while (chunk := file.read(131072)):
        sys.stdout.write("\r")
        sys.stdout.flush()

        await response.send_str(f"WSFS_BLOCK {len(chunk)} {hex(zlib.crc32(chunk))}")
        await response.send_bytes(chunk)

        bytes_sent += len(chunk)

        sys.stdout.write(f"\x1b[2KUploading {path} [{humanize.naturalsize(bytes_sent, format='%.2f')} / {humanize.naturalsize(file_size, format='%.2f')}]")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    await response.send_str("WSFS_EOF")

    msg = await response.receive()
    if msg.data != "WSFS_OK":
        print(f"Server: {msg.data}")
        file.close()
        return False

    file.close()

    return True

async def main():
    session = ClientSession()

    async with session.ws_connect(sys.argv[1]) as response:
        result = False
        if sys.argv[2] == "get":
            result = await client_get(response, sys.argv[3])
        elif sys.argv[2] == "put":
            result = await client_put(response, sys.argv[3], sys.argv[4])
        if not result:
            print(f"Failed to {sys.argv[2]} {sys.argv[3]}")
        await response.close()

    await session.close()

asyncio.run(main())
