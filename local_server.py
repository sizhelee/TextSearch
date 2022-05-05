from multiprocessing.dummy import Process, Lock
from threading import Thread
import socket
from time import sleep
import os
import struct
import numpy as np

from utils import io_util, util


class LocalServer(object):
    def __init__(self, host, port, cfg):
        self.address = (host, port)
        self.documentpath = cfg["path"]["news_fold"]

        self.df = io_util.load_csv(cfg["path"]["news_csv"])
        self.feats = io_util.load_npy(cfg["path"]["news_feats"])
        self.vocab_file = io_util.load_csv(cfg["path"]["vocab_csv"])
        self.similarity = io_util.load_npy(cfg["path"]["news_sim"])
        self.sim_word = io_util.load_json(cfg["path"]["word_sim"])
        self.result_logger = io_util.init_logger(
            cfg["path"]["result_log"], "result")
        self.server_logger = io_util.init_logger(
            cfg["path"]["server_log"], "server")

        self.vocab = list(self.vocab_file.iloc[:, 1])

        self.th_news_sim = cfg["model"]["threshold_news_sim"]
        self.th_news_score = cfg["model"]["threshold_news_score"]
        self.th_news_cos = cfg["model"]["threshold_news_cos"]
        self.buf_size = cfg["model"]["buf_size"]
        self.numnews = cfg["consts"]["num_news"]

        self.documents = []

        io_util.write_log(self.server_logger, "[Server] Successfully init! feat shape: {}".format(
            self.feats.shape), verbose=True)

    def text_search(self, terms, mode=0):
        '''
        文本检索函数
        输入：
            terms：查询文本列表
            mode：查询模式（0普通查询，1模糊查询）
        使用hits算法优化检索
        利用查询结果更新self.documents列表
        '''

        # 模糊检索中更新检索词
        ori_terms = terms
        terms = util.renew_terms(terms, self.sim_word, mode)

        # 用关键词命中一组诗歌
        result = util.cal_simple_score(self.df, terms, self.th_news_score)

        if len(result) > 0:
            # 利用hits算法优化检索
            # 找有关联的文章加入结果集合
            feats = []
            for i in range(self.numnews):
                if i+1 in result:
                    feats.append(self.feats[i])
                else:
                    for j in result:
                        if self.similarity[i][j[0]-1] > self.th_news_sim:
                            feats.append(self.feats[i])
                            break
            feats = np.vstack(feats)

            # 求出新的文章集合的主特征向量
            feat_vec = util.cal_feat_vec(feats)
            cos_new = np.dot(self.feats, feat_vec)

            # 求出与主特征向量的cos结果并降序排列，得到最终的文档集合
            result_new = np.argsort(-cos_new)
            self.documents = []
            for i in result_new:
                if cos_new[i] > self.th_news_cos:
                    self.documents.append(i+1)
                else:
                    break
        else:
            self.documents = []

        io_util.write_log(self.result_logger, "[Server] sim_mode: {}, receive terms {}, search terms {}, return documents {}".format(
            mode, ori_terms, terms, self.documents))

    def func_server(self, conn, terms, lock, mode=0):
        '''
        实现服务器端的功能
        对接收到的词语进行查询，将查询结果文件返回给客户端
        有简单的握手处理
        '''

        lock.acquire()
        io_util.write_log(self.server_logger, "[Server] Func searching_text receive terms: {}".format(
            terms), verbose=True)

        self.text_search(terms, mode)
        io_util.write_log(self.server_logger, "[Server] documents: {}".format(
            self.documents), verbose=True)

        # 得到查询结果后，以文件形式发送给客户端
        str_document = ' '.join(map(lambda x: str(x), self.documents))
        conn.send(str_document.encode())

        file_cnt = 0
        for item in self.documents:

            # 逐一发送文件，每一个文件先发送报头，再发送内容
            file_cnt += 1
            filename = "{}{}.txt".format(self.documentpath, item)
            filesize_bytes = os.path.getsize(filename)
            dirc = {"fileName": "{}.txt".format(item),
                    "fileSize": filesize_bytes}

            head_infor = io_util.dump_json(dirc)
            head_infor_len = struct.pack('i', len(head_infor))

            conn.send(head_infor_len)
            conn.send(head_infor.encode("utf-8"))

            io_util.send_txt(filename, conn)

            # 确认客服端已经收到文件
            completed = conn.recv(self.buf_size).decode("utf-8")
            if completed == "ACK":
                io_util.write_log(self.server_logger,
                                  "[Server] Client download file {} successfully!".format(filename), verbose=True)

            # 判断所有文件是否都已发送
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
            io_util.write_log(
                self.server_logger, "[Server] Waiting for connecting to client...", verbose=True)
            conn, addr = server.accept()
            io_util.write_log(self.server_logger, "[Server] Connected to address {}, socket id: {}".format(
                addr, conn), verbose=True)

            buf = conn.recv(self.buf_size)
            str_terms = buf.decode()

            mode = int(str_terms[0])
            str_terms = str_terms[1:]
            io_util.write_log(self.server_logger, "[Server] received terms: {}, sim_mode: {}".format(
                str_terms, mode), verbose=True)
            terms = str_terms.split(" ")

            p = Process(target=self.func_server, args=(conn, terms, l, mode))
            p.start()


def main():
    config = io_util.load_yaml("./config.yml", True)
    server = LocalServer("0.0.0.0", 1234, config)
    server.run()


if __name__ == "__main__":
    main()
