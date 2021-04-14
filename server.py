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


def handle_client(conn, addr):

    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@CONNECT@Welcome to the server".encode(FORMAT))

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0]

        send_data = ""

        if cmd == "LOGOUT":
            break

        elif cmd == "CREATE":
            files = os.listdir(SERVER_PATH)
            fileName = data[1]

            if fileName in files:  # condition if file already exist in the server.
                send_data = "ERR@CREATE@File exists."
            else:
                buff = b""
                with open(os.path.join(SERVER_PATH, fileName), 'wb') as temp_file:  # creating the file
                    temp_file.write(buff)
                send_data = "OK@CREATE@File created"

            conn.send(send_data.encode(FORMAT))

        elif cmd == "DIR":
            send_data = "OK@DIR@" + '{ "files": [' + \
                ','.join(map(lambda f: json.dumps({
                    'name': f.name,
                    'dir': f.is_dir(),
                    'last_modified': f.stat().st_mtime,
                    'size': f.stat().st_size
                }), [
                    name for name in os.scandir(SERVER_PATH)])) + "] }"

            conn.send(send_data.encode(FORMAT))

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

    print(f"{addr} disconnected")
    conn.close()


def main():
    print("Starting the server")
    # used IPV4 and TCP connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)  # bind the address
    server.listen()  # start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept()  # accept a connection from a client
        thread = threading.Thread(target=handle_client, args=(
            conn, addr))  # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
