from multiprocessing.dummy import Process, Lock
from threading import Thread
import socket
import json
from time import sleep
import os
import struct


class LocalServer(object):
    def __init__(self, host, port):
        self.address = (host, port)
        self.documents = [4, 5, 6]
        self.documentpath = "./preprocess/"

    def func_server(self, conn, terms, lock):
        lock.acquire()
        print("[Server] Func searching_text receive terms: {}".format(terms))
        file_cnt = 0

        str_document = ' '.join(map(lambda x: str(x), self.documents))
        conn.send(str_document.encode())

        for item in self.documents:
            file_cnt += 1
            filename = "{}{}.txt".format(self.documentpath, item)
            filesize_bytes = os.path.getsize(filename)
            dirc = {"fileName": "{}.txt".format(item),
                    "fileSize": filesize_bytes}

            head_infor = json.dumps(dirc)
            head_infor_len = struct.pack('i', len(head_infor))

            conn.send(head_infor_len)
            conn.send(head_infor.encode("utf-8"))

            with open(filename, 'rb') as f:
                data = f.read()
                conn.sendall(data)
                f.close()

            completed = conn.recv(1024).decode("utf-8")
            if completed == "ACK":
                print(
                    "[Server] Client download file {} successfully!".format(filename))

            if file_cnt == len(self.documents):
                conn.send("FIN".encode("utf-8"))
            else:
                conn.send("NOF".encode("utf-8"))

        lock.release()
        conn.close()

    def run(self):

        l = Lock()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.address)
        server.listen(5)

        """
        TODO：请在服务器端实现合理的并发处理方案，使得服务器端能够处理多个客户端发来的请求
        """
        while True:
            print("[Server] Waiting for connecting to client...")
            conn, addr = server.accept()
            print("[Server] Connected to address {}, socket id: {}".format(addr, conn))

            buf = conn.recv(1024)
            str_terms = buf.decode()

            print("[Server] received terms: {}".format(str_terms))
            terms = str_terms.split(" ")

            p = Process(target=self.func_server, args=(conn, terms, l))
            p.start()

        """
        TODO: 请补充实现文本检索，以及服务器端与客户端之间的通信
        
        1. 接受客户端传递的数据， 例如检索词
        2. 调用检索函数，根据检索词完成检索
        3. 将检索结果发送给客户端，具体的数据格式可以自己定义
        
        """


server = LocalServer("0.0.0.0", 1234)
server.run()
