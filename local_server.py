from multiprocessing.dummy import Process, Lock
from threading import Thread
import socket
import json
from time import sleep
import os
import struct
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def cal_news_score(goal, title_cnt, term_cnt):
    return (goal+term_cnt*10)*(title_cnt+1)


def cal_feat_vec(x):
    sc = StandardScaler()
    x_std = sc.fit_transform(x)
    cov_x = np.cov(x_std.T)
    eigen_val, eigen_vec = np.linalg.eig(cov_x)

    pair_x = [(np.abs(eigen_val[i]), eigen_vec[:, i])
              for i in range(len(eigen_val))]
    pair_x.sort(key=lambda k: k[0], reverse=True)
    return pair_x[0][1].reshape(1000)


class LocalServer(object):
    def __init__(self, host, port):
        self.address = (host, port)
        self.documents = []
        self.documentpath = "./server_files/news/"
        self.df = pd.read_csv("./data/all_news.csv")
        self.feats = np.load(
            "./server_files/file_feats_1000.npy", allow_pickle=True)
        self.vocab_file = pd.read_csv("./server_files/vocab.csv")
        self.vocab = list(self.vocab_file.iloc[:, 1])
        self.similarity = np.load("./server_files/similarity.npy")
        self.threshold = 0.1
        self.numnews = 2225

        print("[Server] Successfully init! feat shape: {}".format(self.feats.shape))

    def text_search(self, terms):
        result = []
        for item in self.df.iloc():
            goal = 0
            title_cnt = 0
            term_cnt = 0
            for term in terms:
                if term in item.body:
                    term_cnt += 1
                goal += item.body.count(term)
                title_cnt += item.title.count(term)
            score = cal_news_score(goal, title_cnt, term_cnt)
            if score > 20:
                result.append((int(item.id), score))
        result = sorted(result, key=lambda x: (x[1], x[0]))

        if len(result) > 0:
            feats = []
            for i in range(self.numnews):
                if i+1 in result:
                    feats.append(self.feats[i])
                else:
                    for j in result:
                        if self.similarity[i][j[0]-1] > self.threshold:
                            feats.append(self.feats[i])
                            break
            feats = np.vstack(feats)
            print("[For DEBUG] feats shape: {}".format(feats.shape))
            feat_vec = cal_feat_vec(feats)
            cos_new = np.dot(self.feats, feat_vec)
            result_new = np.argsort(-cos_new)[:10]

            self.documents = [i+1 for i in result_new]
        else:
            self.documents = []

    def func_server(self, conn, terms, lock):
        lock.acquire()
        print("[Server] Func searching_text receive terms: {}".format(terms))

        self.text_search(terms)
        print("[Server] documents: {}".format(self.documents))

        str_document = ' '.join(map(lambda x: str(x), self.documents))
        conn.send(str_document.encode())

        file_cnt = 0
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
