# _*_coding:utf-8_*_
# Developer: Daixiangxiang
# Development Time: 2022-06-03 17:03
# Filename: server.py

import os
import json
import socket
import time

def sendFile(sck, file_path, position):
    '''
    # Send file
    :param sck:
    :param file_path:
    :param position:
    :return:
    '''
    file, type = os.path.splitext(file_path)
    file_size = os.path.getsize(file_path)
    # Construct header dictionary, use json to package and encode
    header = {'filename': file, 'type': type, 'len': file_size}
    # Use gbk encoding
    header_bytes = str.encode(json.dumps(header), encoding='gbk', errors='ignore')
    # According to network protocol, TCP header length, pad to 1024 bytes if not full
    header_bytes += str.encode(' ' * (1024 - len(header_bytes)), encoding='gbk', errors='ignore')
    sck.send(header_bytes)
    sck.recv(1024)
    # The client sends back an empty data each time it receives, the server will wait for the response before sending the next batch of data

    print('\033[1;31m-----------------------------------------------\033[0m')
    print(f'Transmission information for sending file {position}:')
    print(f'header size: {len(header_bytes)}')
    print(f'file size: {file_size}\n')

    with open(file_path, 'rb') as f:
        while file_size:
            # Send 1024 bytes of information each time
            if file_size > 1024:
                msg = f.read(1024)
                file_size -= 1024
            else:
                msg = f.read(file_size)
                file_size = 0
            sck.send(msg)
            sck.recv(1024)
        f.close()
    print(f'File {position} sent successfully')


if __name__ == '__main__':
    print("Server")
    print("Server is waiting for connection requests...")
    # Create socket
    host = '127.0.0.1'
    port = 9999
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create socket
    s.bind((host, port))  # Set the server IP address and port to connect to
    s.listen(5)  # Listen, n indicates the maximum number of connections the OS can hold before refusing connections (queue size)
    conn, addr = s.accept()  # Accept connection request
    print("Connected successfully! Client IP address: " + str(addr[0]) + " Port number: " + str(addr[1]) + "\n")
    # Send 10 files in sequence
    for i in range(1, 11):
        file_path = f'./source/{i}.bin'
        sendFile(conn, file_path, i)
        # time.sleep(0.1)
    time.sleep(5)
    conn.close()
