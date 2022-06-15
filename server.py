# _*_coding:utf-8_*_
# 开发人：戴祥祥
# 开发时间：2022-06-03  17:03
# 文件名：server.py

import os
import json
import socket
import time

def sendFile(sck, file_path, position):
    '''
    #发送文件
    :param sck:
    :param file_path:
    :param position:
    :return:
    '''
    file, type = os.path.splitext(file_path)
    file_size = os.path.getsize(file_path)
    # 构造header字典，使用json打包并编码
    header = {'filename':file, 'type':type, 'len':file_size}
    #编码采用gbk
    header_bytes = str.encode(json.dumps(header), encoding='gbk', errors='ignore')
    # 采用计网的规定，TCP头长度，没满1024就补到1024字节
    header_bytes += str.encode(' '*(1024 - len(header_bytes)), encoding='gbk', errors='ignore')
    sck.send(header_bytes)
    sck.recv(1024)
    #客户端每次接受都会发送回一个空数据，服务端会等到响应才继续发送下一批数据

    print('\033[1;31m-----------------------------------------------\033[0m')
    #print('打印'+f'{file}'+'的传输信息')
    print(f'打印发送文件{position}的传输信息:')
    print(f'header size:{len(header_bytes)}')
    print(f'file size:{file_size}\n')

    with open(file_path, 'rb') as f:
        while file_size:
            # 每次发送1024字节信息
            if file_size > 1024:
                msg = f.read(1024)
                file_size -= 1024
            else:
                msg = f.read(file_size)
                file_size = 0
            sck.send(msg)
            sck.recv(1024)
        f.close()
        # send_size = 0
        # while send_size<file_size:
        #     # 每次发送1024字节信息
        #     msg = f.read(1024)
        #     sck.send(msg)
        #     send_size += 1024
        # f.close()
    print(f'文件{position}发送完毕')


if __name__ == '__main__':
    print("服务器")
    print("服务器正在等待请求连接...")
    # 创建socket
    host = '127.0.0.1'
    port = 9999
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)  # 创建套接字
    s.bind((host, port))# 设置要连接的服务器IP地址和端口
    s.listen(5)  # 监听, n表示的是服务器拒绝(超过限制数量的)连接之前，操作系统可以挂起的最大连接数量。n也可以看作是"排队的数量"
    conn, addr= s.accept()  # 接受连接请求
    print("连接成功!  客户端IP地址:" + str(addr[0]) + "  端口号:" + str(addr[1]) + "\n")
    # 依次发送10个文件
    for i in range(1,11):
        file_path = f'./source/{i}.bin'
        sendFile(conn, file_path, i)
        #time.sleep(0.1)
    time.sleep(5)
    conn.close()
