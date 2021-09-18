import os, sys, zlib, humanize
from aiohttp import web, ClientSession, WSMsgType

if len(sys.argv) < 2:
    print("You need to specify a wsfs root")
    exit()

if not os.path.exists(sys.argv[1]):
    print(f"\"{sys.argv[1]}\" doesnt exist")
    exit()

wsfs_root = sys.argv[1]

async def wsfs_connection(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    cwd = "/"

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            if msg.data == "disconnect":
                await ws.send_str("Connection closed")
                await ws.close()
            elif msg.data == "lsr":
                listing = os.listdir(f"{wsfs_root}{cwd}")
                file_sizes = [os.path.getsize(f"{wsfs_root}{cwd}/{entry}") if not os.path.isdir(f"{wsfs_root}{cwd}/{entry}") else -1 for entry in listing]

                await ws.send_json(list(zip(listing, file_sizes)))
            elif msg.data == "ls":
                listing = os.listdir(f"{wsfs_root}{cwd}")

                buffer = f"Listing of {cwd}\n"
                for entry in listing:
                    if os.path.isdir(f"{wsfs_root}{cwd}/{entry}"):
                        buffer += f"• {entry} -- Directory\n"
                    else:
                        buffer += f"• {entry} -- {humanize.naturalsize(os.path.getsize(wsfs_root + cwd + '/' + entry))}\n"

                await ws.send_str(buffer)
            elif msg.data == "pwd":
                await ws.send_str(cwd)
            elif msg.data.startswith("cd"):
                cmd_data = msg.data.split(" ")

                if len(cmd_data) == 1:
                    await ws.send_str("Please specify a directory")
                    continue

                if cmd_data[1] == "..":
                    split_cwd = cwd.split("/")[:-1]
                    if len(split_cwd) <= 1:
                        cwd = "/"
                    else:
                        cwd = "/".join(split_cwd)

                    continue

                if ".." in cmd_data[1] or cmd_data[1].endswith("."):
                    await ws.send_str("Path contains illegal characters")
                    continue

                if cmd_data[1] != "/" and cmd_data[1].endswith("/"):
                    cmd_data[1] = cmd_data[1][:-1]

                if cmd_data[1].startswith("/"):
                    target = cmd_data[1]
                elif cwd == "/":
                    target = f"{cwd}{cmd_data[1]}"
                else:
                    target = f"{cwd}/{cmd_data[1]}"

                if not os.path.exists(wsfs_root + target):
                    await ws.send_str("Directory doesnt exist")
                    continue

                cwd = target
            else:
                if msg.type == WSMsgType.TEXT:
                    if ".." in msg.data or msg.data.endswith("."):
                        await ws.send_str("Path contains illegal characters")
                        continue

                    if msg.data.startswith("/"):
                        target = f"{wsfs_root}{msg.data}"
                    else:
                        target = f"{wsfs_root}{cwd}/{msg.data}"

                    if not os.path.isfile(target):
                        await ws.send_str("File not found")
                        continue

                    f = open(target, "rb")

                    await ws.send_str(f"WSFS_FILE {os.path.getsize(target)}")

                    while True:
                        data = f.read(131072)
                        if not data:
                            break

                        await ws.send_str(f"WSFS_BLOCK {len(data)} {hex(zlib.crc32(data))}")
                        await ws.send_bytes(data)

                    f.close()

                    await ws.send_str("WSFS_EOF")
        else:
            await ws.send_str("Unknown data type")

    return ws

app = web.Application()
app.add_routes([web.get("/", wsfs_connection)])
web.run_app(app, port=os.environ.get("PORT", 7772))