
# Author : Ayesha S. Dina

import os
import socket


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
    cmd, msg = data.split("@")
    while True:  # multiple communications
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        # elif cmd == "DIR":
        #     print(f"{msg}")

        data = input("> ")
        data = data.split(" ")
        cmd = data[0]

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
        cmd, msg = data.split("@")

    print("Disconnected from the server.")
    client.close()  # close the connection


if __name__ == "__main__":
    main()
