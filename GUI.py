import tkinter as tk
import socket
import json
import struct
import os


class MainPanel:
    def __init__(self, host, port):
        # 用于连接服务器
        self.addr = (host, port)
        self.documents = []
        self.titles = []
        self.FILEPATH = "./user_files/"

    def start(self):
        """
        显示文本检索主界面
        """
        self.root = tk.Tk()
        self.root.geometry('400x400')
        self.root.title("文本检索")
        self.label = tk.Label(self.root, text="请输入检索词，用空格分隔:",
                              font=(None, 12)).pack(pady=20)

        self.new_searchterm_entry = tk.Entry(self.root, font=(None, 12))
        self.new_searchterm_entry.pack()
        self.confirm_button = tk.Button(self.root, text="开始检索", font=(
            None, 12), command=self.check_new_searchterm).pack(pady=40)

        self.hint_label = tk.Label(self.root, text="", font=(None, 12))
        self.hint_label.pack()

        self.root.mainloop()

    def check_new_searchterm(self):
        """
        用户点击"确认"按钮后，检查输入是否合法
        """
        searchterm = self.new_searchterm_entry.get()
        terms = searchterm.split(' ')
        terms = [i for i in terms if i != '']
        if len(terms) == 0 or len(terms) > 3:
            self.hint_label.config(text=f"请输入1-3个检索词")
        else:
            self.search_request(terms)

    def search_request(self, terms):
        """
        TODO: 请补充实现客户端与服务器端的通信

        1. 向服务器发送检索词
        2. 接受服务器返回的检索结果

        """
        str_terms = ' '.join(terms)

        client = socket.socket()
        client.connect(self.addr)
        print("[Client] send terms: {}".format(str_terms))
        client.send(str_terms.encode())

        str_title = client.recv(1024).decode("utf-8")
        self.titles = str_title.split(" ")
        print("[Client] Search Results: {}".format(self.titles))

        while True:

            head_struct = client.recv(4)
            head_len = struct.unpack('i', head_struct)[0]
            data = client.recv(head_len)

            head_dir = json.loads(data.decode('utf-8'))
            filesize_b = head_dir["fileSize"]
            filename = head_dir["fileName"]

            recv_len = 0
            recv_mesg = b''

            f = open("%s%s" % (self.FILEPATH, filename), "wb")

            while recv_len < filesize_b:
                if filesize_b - recv_len > 1024:
                    recv_mesg = client.recv(1024)
                    f.write(recv_mesg)
                    recv_len += len(recv_mesg)
                else:
                    recv_mesg = client.recv(filesize_b - recv_len)
                    recv_len += len(recv_mesg)
                    f.write(recv_mesg)
                    f.close()
                    print("[Client] Successfully receive files!")

            # 向服务器发送信号，文件已经上传完毕
            completed = "ACK"
            client.send(bytes(completed, "utf-8"))

            file_finish = client.recv(4).decode("utf-8")
            if file_finish == "FIN":
                break

        client.close()

        self.documents = []
        for title in self.titles:
            filename = "{}{}.txt".format(self.FILEPATH, title)
            with open(filename, "r") as f:
                str_title = f.readline()
                str_content = f.read()
                self.documents.append((str_title, str_content))

        # 这里暂且假设获得的检索结果存储在self.documents中，并且数据格式为[(title1, doc1), (title2, doc2), ...]
        # 具体形式可以自由修改（下面几个函数中的对应内容也需要改一下）

        # 展示检索结果
        self.show_titles()

    def show_titles(self):
        """
        显示所有相关的文章

        1. 显示根据检索词搜索到的所有文章标题，使用滚动条显示（tkinter的Scrollbar控件）
        2. 点击标题，显示文章的具体内容（这里使用了 Listbox 控件的bind方法，动作为 <ListboxSelect>)

        """
        self.title_tk = tk.Tk()
        self.title_tk.geometry("300x300")
        self.title_tk.title("检索结果")
        self.show_listbox(self.title_tk, self.documents)

    def show_listbox(self, title_tk, documents):
        self.scrollbar = tk.Scrollbar(title_tk)
        self.scrollbar.pack(side='right', fill='both')
        self.listbox = tk.Listbox(
            title_tk, yscrollcommand=self.scrollbar.set, font=(None, 12))

        for doc in documents:
            self.listbox.insert("end", str(doc[0]))
        self.listbox.bind('<<ListboxSelect>>', self.show_content(documents))
        self.listbox.pack(side='left', fill='both', expand=True)

    def show_content(self, documents):
        """
        显示文档的具体内容
        """
        def callback(event):
            idx = event.widget.curselection()[0]
            content_tk = tk.Tk()
            content_tk.geometry("300x300")
            content_tk.title("显示全文")
            # print(self.documents[idx])
            text = tk.Text(content_tk, font=(None, 12))
            text.config(spacing1=10)  # 调整一下行间距
            text.config(spacing2=5)
            for item in documents[idx]:
                text.insert("end", str(item) + '\n')
            text["state"] = 'disabled'
            text.pack()

        return callback


if __name__ == "__main__":

    dirs = "./user_files"
    if not os.path.exists(dirs):
        os.mkdir(dirs)

    host = '127.0.0.1'
    port = 1234
    gui = MainPanel(host, port)
    gui.start()
