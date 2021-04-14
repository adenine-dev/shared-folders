import os
import socket
import json
import sys
import datetime
from functools import reduce

# IP = "192.168.1.101" #"localhost"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024  # byte .. buffer size
FORMAT = "utf-8"
CLIENT_PATH = "client"


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    data = client.recv(SIZE).decode(FORMAT)
    # all responses are made up of status@command@data, status is always OK or ERR, command is always a command, and data is any string of data.
    status, cmd, res = data.split("@")

    while True:
        if status == "OK":
            if cmd == "CREATE" or cmd == "DELETE" or cmd == "UPLOAD_END":
                print(f"{res}")

            elif cmd == "DIR":
                # TODO: maybe change the way this is printed (more data, kb/mb instead of just bytes?)
                res = json.loads(res)
                l = reduce(lambda a, c: max(
                    a, len(c['name'])), res["files"], 0)
                print(f"{'filename':<{l}} | modified | size (bytes)")
                print('-'*(l + 26))
                for file in res["files"]:
                    modified = datetime.datetime.fromtimestamp(
                        file['last_modified'])
                    print(
                        f"{file['name']:<{l}} | {f'{modified.hour:02}:{modified.minute:02}':<8} | {file['size']:<8}")

            elif cmd == "UPLOAD":
                file = open(os.path.join(CLIENT_PATH, res))

                fragment = file.read(1024 - 12)
                while fragment:
                    client.send(f"UPLOAD_DATA@{fragment}".encode(FORMAT))
                    fragment = file.read(1024 - 12)

                file.close()
                client.send("UPLOAD_END".encode(FORMAT))

                data = client.recv(SIZE).decode(FORMAT)
                status, cmd, res = data.split("@")

                continue

        elif status == "ERR":  # assume all errors are just messages for now.
            print(f"{res}")

        data = input("> ")
        data = data.split(" ")
        cmd = data[0].upper()

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))

        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        # elif cmd == "CREATE":
        #     print(f"{cmd}@{data[1]}")
        #     client.send(f"{cmd}@{data[1]}".encode(FORMAT))

        elif cmd == "UPLOAD":
            try:
                if data[1] in os.listdir(CLIENT_PATH):
                    client.send(f"{cmd}@{data[1]}".encode(FORMAT))
                else:
                    print("File does not exist.")
            except:
                print(sys.exc_info()[0])

        elif cmd == "DIR":
            client.send(cmd.encode(FORMAT))

        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))

        else:
            print("invalid command")
            continue

        data = client.recv(SIZE).decode(FORMAT)
        status, cmd, res = data.split("@")

    print("Disconnected from the server.")
    client.close()  # close the connection


if __name__ == "__main__":
    main()
