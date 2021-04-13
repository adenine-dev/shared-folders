import os
import socket
import json
import sys
import datetime

# IP = "192.168.1.101" #"localhost"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024  # byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    data = client.recv(SIZE).decode(FORMAT)
    status, cmd, res = data.split("@")
    while True:  # multiple communications
        if status == "OK":
            if cmd == "CREATE":
                print(f"{res}")
            elif cmd == "DIR":
                # TODO: maybe change the way this is printed (more data, kb/mb instead of just bytes?)
                res = json.loads(res)
                print(f"{'filename':<16} | modified | size (bytes)")
                print(f"------------------------------------------")
                for file in res["files"]:
                    modified = datetime.datetime.fromtimestamp(
                        float(file['last_modified']))
                    print(
                        f"{file['filename']:<16} | {f'{modified.hour:02}:{modified.minute:02}':<8} | {file['size']:<8}")
        elif status == "ERR":  # assume all errors are just messages for now.
            print(f"{res}")
        elif cmd == "DISCONNECTED":
            print(f"{res}")
            break

        data = input("> ")
        data = data.split(" ")
        cmd = data[0].upper()

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))

        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        elif cmd == "CREATE":
            # two words are separated by @ character.
            print(f"{cmd}@{data[1]}")
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))

        elif cmd == "DIR":
            client.send(cmd.encode(FORMAT))
        else:
            print("invalid command")
            continue

        data = client.recv(SIZE).decode(FORMAT)
        status, cmd, res = data.split("@")

    print("Disconnected from the server.")
    client.close()  # close the connection


if __name__ == "__main__":
    main()
    input()
