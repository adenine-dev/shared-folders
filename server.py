import os
import socket
import threading
import json
import sys


IP = "localhost"  # 192.168.1.101
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
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

    active_filename = ""
    active_file = None
    active_command = ""

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@", 1)
        cmd = data[0]

        send_data = ""

        if cmd == "LOGOUT":
            break

        elif cmd == "CREATE":
            files = os.listdir(SERVER_PATH)
            filename = data[1]

            if filename in files:  # condition if file already exist in the server.
                send_data = "ERR@CREATE@File exists."
            else:
                buff = b""
                with open(os.path.join(SERVER_PATH, filename), 'wb') as temp_file:  # creating the file
                    temp_file.write(buff)
                send_data = "OK@CREATE@File created"

            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            filename = data[1]

            if filename in os.listdir(SERVER_PATH):
                send_data = "ERR@UPLOAD@File exists."
            else:
                active_filename = filename
                active_file = open(os.path.join(
                    SERVER_PATH, active_filename), 'w')

                active_command = "UPLOAD"
                send_data = f"OK@UPLOAD@{active_filename}"

            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD_DATA":
            if active_file and active_command == "UPLOAD":
                active_file.write(data[1])

        elif cmd == "UPLOAD_END":
            if active_file and active_command == "UPLOAD":
                active_file.close()
                conn.send(
                    f"OK@UPLOAD_END@Successfully uploaded file".encode(FORMAT))

                print("done")
                active_file = None
                active_command = ""
                active_filename = ""

        elif cmd == "DOWNLOAD":
            filename = data[1]

            if filename not in os.listdir(SERVER_PATH):
                conn.send("ERR@DOWNLOAD@File does not exist.".encode(FORMAT))
            else:
                conn.send(f"OK@DOWNLOAD@{filename}".encode(FORMAT))

                file = open(os.path.join(SERVER_PATH, filename))
                fragment = file.read(SIZE - 14)
                while fragment:
                    conn.send(f"DOWNLOAD_DATA@{fragment}".encode(FORMAT))
                    fragment = file.read(SIZE - 14)
                    data = conn.recv(SIZE).decode(FORMAT)

                file.close()
                conn.send("DOWNLOAD_END@".encode(FORMAT))

        elif cmd == "DIR":
            print("sucks")
            #send_data = "OK@DIR@" + '{ "files": [' + \
            #   ','.join(map(lambda f: json.dumps({
             #       'name': f.name,
             #       'dir': f.is_dir(),
            #        'last_modified': f.stat().st_mtime,
            #        'size': f.stat().st_size
            #    }), [
            #        name for name in os.scandir(SERVER_PATH)])) + "] }"

            #conn.send(send_data.encode(FORMAT))

        elif cmd == "DELETE":
            files = os.listdir(SERVER_PATH)
            filename = data[1]

            if filename not in files:  # condition if file already exist in the server.
                send_data = f"ERR@DELETE@{filename} does not exist."
            else:
                try:
                    os.remove(os.path.join(SERVER_PATH, filename))
                    send_data = f"OK@DELETE@{filename} deleted successfully"
                except:
                    print(sys.exc_info()[0])
                    send_data = f"ERR@DELETE@{filename} failed to be deleted."

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
