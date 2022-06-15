# _*_coding:utf-8_*_
# 开发人：戴祥祥
# 开发时间：2022-06-03  17:03
# 文件名：client.py
import os
import cv2
import json

import socket
import threading
import numpy as np
import queue
import time

FPS=30
#图像属性
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
        # 指定FPS和一个缓冲队列
        self.fps = fps
        self.que = queue.Queue(0)
    #分支：取队列数据播放
    def run(self) -> None:
        while True:
            try:# try except原因是缓冲队列超时后会引起异常，通过超时信号判断队列已空
                frame = self.que.get(True, 1)
                cv2.imshow('video', frame)
                # 等待时间 1/fps s，下面函数的单位是毫秒所以用1000，实现帧率控制
                key = cv2.waitKey(1000//self.fps)
                # 退出播放
                if key == ord('q'):
                    exit(0)
            except: #缓冲队列超时，队列空了
                print('over')
                break


def recvFile(sck, file_path, position):
    '''
    接收文件，并储存
    :param sck:
    :param file_path:
    :param position:
    :return:
    '''

    header = json.loads(sck.recv(1024).decode('gbk', errors='ignore'))
    sck.send(json.dumps(' ' * 1024).encode())#new
    file_size = header['len']
    print(f'打印接收文件{position}的传输信息:')
    print(f'filename:{header["filename"] + header["type"]}')
    print(f'file size:{file_size}')
    print('\033[1;31m-----------------------------------------------\033[0m')
    with open(file_path, 'wb') as f:
        while file_size:
            if file_size >= 1024:
                msg = sck.recv(1024)
                file_size -= 1024
            # 最后一个文件块就按剩余大小发送,以防文件尾部和下一个头部拼成1024一起读进来
            else:
                msg = sck.recv(file_size)
                file_size = 0
            sck.send(json.dumps(' ' * 1024).encode())
            #客户端每次接受都会发送回一个空数据，服务端会等到这个响应才继续发送下一批数据；
            #socket的缓冲区就只有1024字节，发快了就会覆盖还没有接受的数据
            f.write(msg)
        f.close()
        # recv_size = 0
        # while recv_size < file_size:
        #     msg = sck.recv(1024)
        #     f.write(msg)
        #     recv_size += 1024
        # f.close()


def from_I420(yuv_data, frames):
    '''
    得到YUV分量
    :param yuv_data:
    :param frames:
    :return: YUV分量
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


def np_yuv2rgb(Y,U,V):
    '''
    numpy数组运算进行加速（速度非常快，使用for循环逐点提取YUV值转换成RGB（非常耗时，不建议使用）
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

    c = (Y-np.array([16])) * 298
    d = U - np.array([128])
    e = V - np.array([128])

    r = (c + 409 * e + 128) // 256
    g = (c - 100 * d - 208 * e + 128) // 256
    b = (c + 516 * d + 128) // 256

    r = np.where(r < 0, 0, r)
    r = np.where(r > 255,255,r)

    g = np.where(g < 0, 0, g)
    g = np.where(g > 255,255,g)

    b = np.where(b < 0, 0, b)
    b = np.where(b > 255,255,b)

    bgr_data[:, :, 2] = r
    bgr_data[:, :, 1] = g
    bgr_data[:, :, 0] = b

    return bgr_data

if __name__ == '__main__':
    print("客户端")
    print("发送视频请求")
    print("连接中...")

    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建TCP套接字
    c.connect(('127.0.0.1', 9999))  # 设置要连接的服务器IP地址和端口
    print("连接成功!")
    print('\033[1;31m------------------------------------------------\033[0m')

    #接收文件
    # for i in range(1, 11):
    #     file_path = f'./receive/{i}.bin'
    #     recvFile(c, file_path, i)

    #双线程，边下载转码边播放
    player = Player(FPS)# 设定FPS，线程分支
    player.start()
    #主程序：接收文件
    for i in range(1, 11):
        file_path = f'./receive/{i}.bin'
        #recvFile(c, file_path, i)
        recvFile(c, file_path, i)
        yuv_path = f'./decode/{i}.yuv'
        os.system(f'TAppDecoder.exe -b {file_path} -o {yuv_path}') #二进制流转YUV420
        #time.sleep(0.25) 开启后不会播放，睡眠进程
        frames = int(os.path.getsize(yuv_path) / IMG_SIZE) #帧数
        with open(yuv_path, 'rb') as fp:
            data = np.frombuffer(fp.read(), np.uint8)
            Y, U, V = from_I420(data, frames)
            for j in range(frames):
                #转换图片格式入队
                player.que.put(np_yuv2rgb(Y[j, :, :], U[j, :, :], V[j, :, :]))
    print('\033[1;31m-----------------------------------------------\033[0m')
    print('视频下载完毕')
    player.join()
