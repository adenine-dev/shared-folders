import os
import socket
import json
import sys
from datetime import datetime, timedelta
from functools import reduce
import math

IP = "localhost"  # 192.168.1.101
PORT = 4450
ADDR = (IP, PORT)
SIZE = 2**12
FORMAT = "utf-8"
CLIENT_PATH = "client"

LOGIN = "admin"
PASS = "admin"


def main():
    start_time = None
    end_time = None
    log_file = open(f"client_log_{datetime.now().timestamp()}", "w")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)
    try:
        client.connect(ADDR)
    except socket.timeout:
        print("Socket Timeout.")
        log_file.write(f"[{datetime.now()}] Socket timed out\n")
        return
    except:
        print("Connection Error.")
        log_file.write(f"[{datetime.now()}] Connection Error\n")
        return

    data = client.recv(SIZE).decode(FORMAT)
    status, cmd, res = data.split("@", 3)
    if status == "ERR":
        print("Connection failed.")
        log_file.write(f"[{datetime.now()}] Connection Failed\n")

    client.send(f"{LOGIN}@{PASS}".encode(FORMAT))

    data = client.recv(SIZE).decode(FORMAT)
    # all responses are made up of status@command@data, status is always OK or ERR, command is always a command, and data is any string of data.
    status, cmd, res = data.split("@", 3)

    cwd = ""

    if status == "ERR":
        print("Server login failed.")
        loggedIn = False
    else:
        loggedIn = True

    while True:
        data = input(f"SERVER/{cwd} > ")
        start_time = datetime.now()
        log_file.write(f"[{start_time}] `{data}` ")

        data = data.split(" ")
        cmd = data[0].upper()
        if cmd == "QUIT":
            break

        if loggedIn == True:
            if cmd == "LOGOUT":
                client.send(cmd.encode(FORMAT))
                loggedIn = False
                print("Disconnected from the server.")

            elif cmd == "UPLOAD":
                try:
                    if data[1] in os.listdir(os.path.join(CLIENT_PATH, cwd)):
                        client.send(
                            f"{cmd}@{data[1]}@{math.ceil(os.path.getsize(os.path.join(CLIENT_PATH, cwd, data[1])) / SIZE)}".encode(FORMAT))
                    else:
                        print("File does not exist.")
                        continue
                except:
                    print(sys.exc_info()[0])

            elif cmd == "DOWNLOAD":
                client.send(f"{cmd}@{data[1]}".encode(FORMAT))

            elif cmd == "DIR":
                client.send(cmd.encode(FORMAT))

            # All of these commands produce practically the same result, insofar as they will send the same structure of data to the server.
            elif cmd == "DELETE" or cmd == "MKDIR" or cmd == "CD" or cmd == "RMDIR":
                if len(data) == 2 and data[1] != "":
                    client.send(f"{cmd}@{data[1]}".encode(FORMAT))
                else:
                    print(f"invalid command syntax, {cmd} file")
                    continue
            else:
                print("invalid command")
                log_file.write(f"-> INVALID\n")

                continue
        else:
            if cmd == "LOGOUT":
                continue
            if cmd == "CONNECT":

                if len(data) != 3 or data[1] == "" or data[2] == "":
                    print("Invalid use of command.")
                    continue

                ip = data[1]
                try:
                    port = (int(data[2]))
                except:
                    print("Invalid Port")
                    continue
                addr = (ip, port)

                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect(addr)

                    data = client.recv(SIZE).decode(FORMAT)
                    status, cmd, res = data.split("@", 3)

                    if status == "OK":
                        login = input("Login: ")
                        password = input("Password: ")

                        client.send(f"{login}@{password}".encode(FORMAT))
                        data = client.recv(SIZE).decode(FORMAT)
                        status, cmd, res = data.split("@", 3)

                        if status == "ERR":
                            print("Server login failed.")
                            loggedIn = False
                        else:
                            loggedIn = True
                        continue

                    else:
                        print("Server Connection Failed.")
                        continue

                except:
                    print("Connection Failed, please try again.")
                    loggedIn = False
                    continue

            else:
                print("You must be connected to a server to preform this action.")
                continue

        if loggedIn == True:
            try:
                data = client.recv(SIZE).decode(FORMAT)
            except socket.timeout:
                print("Socket timed out.")
                continue
            status, cmd, res = data.split("@", 2)

            if status == "OK":
                if cmd == "CREATE" or cmd == "DELETE" or cmd == "UPLOAD_END" or cmd == "MKDIR" or cmd == "RMDIR":
                    print(f"{res}")

                elif cmd == "CD":
                    if res == ".":  # for pretty
                        cwd = ""
                    else:
                        cwd = res.replace("\\", "/")

                elif cmd == "DIR":
                    # TODO: maybe change the way this is printed (more data, kb/mb instead of just bytes?)
                    res = json.loads(res)
                    l = reduce(lambda a, c: max(
                        a, len(c['name'])), res["files"], 0)
                    print(f"{'filename':<{l}} | {'modified':<{16}} | size (bytes)")
                    print('-'*(l + 34))
                    for file in res["files"]:
                        modified = datetime.fromtimestamp(
                            file['last_modified'])
                        print(
                            f"{file['name']:<{l}} | {f'{modified.day:02}/{modified.month:02}/{modified.year:04} {modified.hour:02}:{modified.minute:02}'} | {file['size']:<8}")

                    end_time = datetime.now()

                elif cmd == "UPLOAD":

                    file = open(os.path.join(CLIENT_PATH, cwd, res), "rb")

                    fragment = file.read(SIZE)
                    while fragment:
                        client.send(fragment)
                        fragment = file.read(SIZE)

                    file.close()
                    data = client.recv(SIZE).decode(FORMAT)
                    status, cmd, res = data.split("@")
                    if status == "OK":  # no error state?
                        print(res)

                elif cmd == "DOWNLOAD":
                    active_file = None
                    filename = res.split("@")[0]
                    fragments = int(res.split("@")[1])

                    if filename in os.listdir(os.path.join(CLIENT_PATH, cwd)):
                        active_file = open(os.path.join(
                            CLIENT_PATH, cwd, filename), "wb")
                    else:
                        active_file = open(os.path.join(
                            CLIENT_PATH, cwd, filename), "xb")

                    last_time = datetime.now()
                    log_file.write("\n")
                    for i in range(fragments):
                        data = client.recv(SIZE)
                        active_file.write(data)

                        next_time = datetime.now()

                        if (next_time - last_time).microseconds != 0 and i % 20 == 0:
                            # microseconds for precision, translating to mb/s from b/us is the same as multiplying by 1
                            rate = (SIZE / (next_time - last_time).microseconds)
                            log_file.write(
                                f"\t{next_time}\t\t{(next_time - last_time).microseconds}\t\t{rate}\n")

                            sys.stdout.write(
                                f"\rspeed (mB/s): {rate:.2f}\t\t\t")
                            sys.stdout.flush()

                        last_time = datetime.now()

                    sys.stdout.write("\n")

                    active_file.close()

                    print("file downloaded successfully")

            elif status == "ERR":  # assume all errors are just messages for now.
                print(f"{res}")

            end_time = datetime.now()
            log_file.write(
                f"-> {status} (duration: {end_time - start_time}) [{end_time}]\n")

    client.close()  # close the connection
    log_file.close()


if __name__ == "__main__":
    main()
