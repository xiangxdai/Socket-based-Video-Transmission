# _*_coding:utf-8_*_
# Developer: Daixiangxiang
# Development Time: 2022-06-03 17:03
# Filename: client.py
import os
import cv2
import json

import socket
import threading
import numpy as np
import queue
import time

FPS = 30
# Image properties
IMG_WIDTH = 832
IMG_HEIGHT = 480
IMG_SIZE = int(IMG_WIDTH * IMG_HEIGHT * 3 / 2)

Y_WIDTH = IMG_WIDTH
Y_HEIGHT = IMG_HEIGHT
Y_SIZE = int(Y_WIDTH * Y_HEIGHT)

U_V_WIDTH = int(IMG_WIDTH / 2)
U_V_HEIGHT = int(IMG_HEIGHT / 2)
U_V_SIZE = int(U_V_WIDTH * U_V_HEIGHT)


class Player(threading.Thread):
    def __init__(self, fps):
        threading.Thread.__init__(self)
        # Specify FPS and a buffer queue
        self.fps = fps
        self.que = queue.Queue(0)
    
    # Branch: Retrieve data from the queue and play
    def run(self) -> None:
        while True:
            try:  # try except to handle queue timeout which causes an exception, use the timeout signal to determine if the queue is empty
                frame = self.que.get(True, 1)
                cv2.imshow('video', frame)
                # Wait time 1/fps seconds, the unit of the following function is milliseconds so use 1000 to achieve frame rate control
                key = cv2.waitKey(1000 // self.fps)
                # Exit playback
                if key == ord('q'):
                    exit(0)
            except:  # Queue timeout, queue is empty
                print('over')
                break


def recvFile(sck, file_path, position):
    '''
    Receive file and save it
    :param sck:
    :param file_path:
    :param position:
    :return:
    '''

    header = json.loads(sck.recv(1024).decode('gbk', errors='ignore'))
    sck.send(json.dumps(' ' * 1024).encode())  # new
    file_size = header['len']
    print(f'Transmission information for receiving file {position}:')
    print(f'filename:{header["filename"] + header["type"]}')
    print(f'file size:{file_size}')
    print('\033[1;31m-----------------------------------------------\033[0m')
    with open(file_path, 'wb') as f:
        while file_size:
            if file_size >= 1024:
                msg = sck.recv(1024)
                file_size -= 1024
            # For the last file block, send according to the remaining size to prevent the tail of the file from being read together with the next header into 1024
            else:
                msg = sck.recv(file_size)
                file_size = 0
            sck.send(json.dumps(' ' * 1024).encode())
            # The client sends back an empty data each time it receives, the server will wait for this response before sending the next batch of data;
            # The buffer of the socket is only 1024 bytes, if sent too fast it will overwrite the data that has not been received
            f.write(msg)
        f.close()


def from_I420(yuv_data, frames):
    '''
    Get YUV components
    :param yuv_data:
    :param frames:
    :return: YUV components
    '''

    Y = np.zeros((frames, IMG_HEIGHT, IMG_WIDTH), dtype=np.uint8)
    U = np.zeros((frames, U_V_HEIGHT, U_V_WIDTH), dtype=np.uint8)
    V = np.zeros((frames, U_V_HEIGHT, U_V_WIDTH), dtype=np.uint8)

    for frame_idx in range(0, frames):
        y_start = frame_idx * IMG_SIZE
        u_start = y_start + Y_SIZE
        v_start = u_start + U_V_SIZE
        v_end = v_start + U_V_SIZE

        Y[frame_idx, :, :] = yuv_data[y_start : u_start].reshape((Y_HEIGHT, Y_WIDTH))
        U[frame_idx, :, :] = yuv_data[u_start : v_start].reshape((U_V_HEIGHT, U_V_WIDTH))
        V[frame_idx, :, :] = yuv_data[v_start : v_end].reshape((U_V_HEIGHT, U_V_WIDTH))
    return Y, U, V


def np_yuv2rgb(Y, U, V):
    '''
    Use numpy array operations for acceleration (very fast, avoid using for loops to extract YUV values point by point for RGB conversion which is very time-consuming)
    :param Y:
    :param U:
    :param V:
    :return: bgr_data
    '''
    bgr_data = np.zeros((IMG_HEIGHT, IMG_WIDTH, 3), dtype=np.uint8)
    V = np.repeat(V, 2, 0)
    V = np.repeat(V, 2, 1)
    U = np.repeat(U, 2, 0)
    U = np.repeat(U, 2, 1)

    c = (Y - np.array([16])) * 298
    d = U - np.array([128])
    e = V - np.array([128])

    r = (c + 409 * e + 128) // 256
    g = (c - 100 * d - 208 * e + 128) // 256
    b = (c + 516 * d + 128) // 256

    r = np.where(r < 0, 0, r)
    r = np.where(r > 255, 255, r)

    g = np.where(g < 0, 0, g)
    g = np.where(g > 255, 255, g)

    b = np.where(b < 0, 0, b)
    b = np.where(b > 255, 255, b)

    bgr_data[:, :, 2] = r
    bgr_data[:, :, 1] = g
    bgr_data[:, :, 0] = b

    return bgr_data

if __name__ == '__main__':
    print("Client")
    print("Sending video request")
    print("Connecting...")

    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
    c.connect(('127.0.0.1', 9999))  # Set the IP address and port of the server to connect to
    print("Connected successfully!")
    print('\033[1;31m------------------------------------------------\033[0m')

    # Receive file
    # for i in range(1, 11):
    #     file_path = f'./receive/{i}.bin'
    #     recvFile(c, file_path, i)

    # Two threads, download and decode while playing
    player = Player(FPS)  # Set FPS, thread branch
    player.start()
    # Main program: Receive file
    for i in range(1, 11):
        file_path = f'./receive/{i}.bin'
        recvFile(c, file_path, i)
        yuv_path = f'./decode/{i}.yuv'
        os.system(f'TAppDecoder.exe -b {file_path} -o {yuv_path}')  # Binary stream to YUV420
        # time.sleep(0.25) Enabling this will not play, sleep process
        frames = int(os.path.getsize(yuv_path) / IMG_SIZE)  # Number of frames
        with open(yuv_path, 'rb') as fp:
            data = np.frombuffer(fp.read(), np.uint8)
            Y, U, V = from_I420(data, frames)
            for j in range(frames):
                # Convert image format into queue
                player.que.put(np_yuv2rgb(Y[j, :, :], U[j, :, :], V[j, :, :]))
    print('\033[1;31m-----------------------------------------------\033[0m')
    print('Video download complete')
    player.join()
