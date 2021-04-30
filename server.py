import os
import socket
import threading
import json
import sys
import math

IP = socket.gethostbyname_ex(socket.gethostname())[-1][-1]
PORT = 4450
ADDR = (IP, PORT)
SIZE = 2**10
FORMAT = "utf-8"
SERVER_PATH = "server"

LOGIN = "admin"
PASS = "admin"


def handle_client(conn, addr):

    print(f"[NEW CONNECTION] {addr} is attempting to connect.")
    conn.send("OK@CONNECT@SUCCEED!".encode(FORMAT))

    data = conn.recv(SIZE).decode(FORMAT)
    data = data.split("@", 1)
    login = data[0]
    password = data[1]
    if login == LOGIN and password == PASS:
        print(f"[NEW CONNECTION] {addr} logged in successfully.")
        conn.send("OK@CONNECT@Welcome to the server".encode(FORMAT))
    else:
        conn.send("ERR@CONNECT@LoginFailed".encode(FORMAT))
        print(f"[FAILED CONNECTION] {addr} login/password refused.")
        conn.close()

    cwd = SERVER_PATH

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@", 1)
        cmd = data[0]

        send_data = ""

        if cmd == "LOGOUT":
            break

        elif cmd == "CREATE":
            files = os.listdir(cwd)
            filename = data[1]

            if filename in files:  # condition if file already exist in the server.
                send_data = "ERR@CREATE@File exists."
            else:
                buff = b""
                with open(os.path.join(cwd, filename), 'wb') as temp_file:  # creating the file
                    temp_file.write(buff)
                send_data = "OK@CREATE@File created"

            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            filename = data[1].split("@")[0]
            numbytes = int(data[1].split("@")[1])

            active_file = None
            if filename in os.listdir(os.path.join(cwd)):
                active_file = open(os.path.join(
                    cwd, filename), "wb")
            else:
                active_file = open(os.path.join(
                    cwd, filename), "xb")

            conn.send(f"OK@UPLOAD@{filename}".encode(FORMAT))

            received = 0
            while received < numbytes:
                data = conn.recv(SIZE)
                received += len(data)
                active_file.write(data)

            active_file.close()
            conn.send(
                f"OK@UPLOAD_END@Successfully uploaded file".encode(FORMAT))

            print(f"[FILE TRANSFER] {addr} uploaded file.")

        elif cmd == "DOWNLOAD":
            filename = data[1]

            if filename not in os.listdir(cwd):
                conn.send("ERR@DOWNLOAD@File does not exist.".encode(FORMAT))
            else:
                numbytes = os.path.getsize(os.path.join(cwd, filename))
                conn.send(
                    f"OK@DOWNLOAD@{filename}@{numbytes}".encode(FORMAT))

                file = open(os.path.join(cwd, filename), "rb")

                fragment = file.read(SIZE)
                while fragment:
                    conn.send(fragment)
                    fragment = file.read(SIZE)

                # d = conn.recv(SIZE)

                file.close()

            print(f"[FILE TRANSFER] {addr} downloaded file.")

        elif cmd == "DIR":
            send_data = "OK@DIR@" + '{ "files": [' + \
                ','.join(map(lambda f: json.dumps({
                    'name': f.name,
                    'dir': f.is_dir(),
                    'last_modified': f.stat().st_mtime,
                    'size': f.stat().st_size
                }), [
                    name for name in os.scandir(cwd)])) + "] }"

            conn.send(send_data.encode(FORMAT))

        elif cmd == "DELETE":
            files = os.listdir(cwd)
            filename = data[1]

            if filename not in files:  # condition if file already exist in the server.
                send_data = f"ERR@DELETE@{filename} does not exist."
            else:
                try:
                    os.remove(os.path.join(cwd, filename))
                    send_data = f"OK@DELETE@{filename} deleted successfully"
                except:
                    # print(sys.exc_info()[0])
                    send_data = f"ERR@DELETE@{filename} failed to be deleted."

            conn.send(send_data.encode(FORMAT))

        elif cmd == "MKDIR":
            foldername = data[1].rstrip("./\\").lstrip("./\\")

            if ".." in foldername or "/" in foldername or "\\" in foldername:
                send_data = "ERR@MKDIR@Invalid path name."
            else:
                files = os.listdir(cwd)
                if foldername in files:
                    send_data = "ERR@MKDIR@Folder already exists."
                else:
                    os.mkdir(os.path.join(cwd, foldername))
                    send_data = f"OK@MKDIR@{foldername} created."

            conn.send(send_data.encode(FORMAT))

        elif cmd == "RMDIR":
            foldername = data[1].rstrip("/\\").lstrip("/\\")

            if ".." in foldername or "/" in foldername or "\\" in foldername:
                send_data = "ERR@RMDIR@Invalid path name."
            else:
                files = os.listdir(cwd)
                if foldername not in files:
                    send_data = "ERR@RMDIR@Folder does not exist."
                elif os.path.isfile(os.path.join(cwd, foldername)):
                    send_data = "ERR@RMDIR@File is not a folder."
                else:
                    try:
                        os.rmdir(os.path.join(cwd, foldername))
                        send_data = f"OK@RMDIR@{foldername} deleted."
                    except OSError:
                        send_data = f"ERR@RMDIR@Folder not empty."

            conn.send(send_data.encode(FORMAT))

        elif cmd == "CD":
            foldername = data[1].rstrip("/\\").lstrip("/\\")

            if os.path.abspath(os.path.join(cwd, foldername)).startswith(
                    os.path.abspath(SERVER_PATH)):
                cwd = os.path.normpath(os.path.join(cwd, foldername))
                send_data = f"OK@CD@{os.path.relpath(cwd, SERVER_PATH)}"

            else:
                send_data = f"ERR@CD@Path does not exist"

            conn.send(send_data.encode(FORMAT))

    print(f"[LOST CONNECTION] {addr} disconnected from the server.")
    conn.close()


def main():
    print("Starting the server")
    # used IPV4 and TCP connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)  # bind the address
    server.listen()  # start listening
    print(f"Server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept()  # accept a connection from a client
        thread = threading.Thread(target=handle_client, args=(
            conn, addr))  # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
