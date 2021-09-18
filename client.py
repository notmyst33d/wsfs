import os, asyncio, zlib, sys, time, humanize
from aiohttp import ClientSession, WSMsgType

async def main():
    session = ClientSession()

    async with session.ws_connect(sys.argv[1]) as response:
        await response.send_str(sys.argv[2])

        msg = await response.receive()

        if not msg.data.startswith("WSFS_FILE"):
            print("File not found")
            await response.close()
            await session.close()
            exit()

        file_data = msg.data.split(" ")
        print(f"Received a file with a size of {humanize.naturalsize(file_data[1], format='%.2f')}")

        f = open("wsfs_" + sys.argv[2], "wb")

        total_size = 0

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

            total_size += int(block_data[1])

            f.write(msg.data)

            sys.stdout.write(f"\x1b[2K - Downloading {sys.argv[2]} [{humanize.naturalsize(total_size, format='%.2f')} / {humanize.naturalsize(file_data[1], format='%.2f')}]")
            sys.stdout.flush()

        sys.stdout.write("\n")
        sys.stdout.flush()

        print(f"Took {round(time.time() - stime, 1)} seconds to receive {humanize.naturalsize(file_data[1], format='%.2f')}")

        await response.send_str("disconnect")

        f.close()
        await response.close()

    await session.close()

asyncio.run(main())