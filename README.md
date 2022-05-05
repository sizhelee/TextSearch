# TextSearch

2022春 《Python程序设计与数据科学导论》期中作业

## 介绍

利用基于Tkinter的Server-Client架构和HITS算法实现文本检索模型

在模型实现中，我们采用了关键词匹配、HITS优化排序、模糊匹配三种检索算法，并在GUI界面中提供优化排序和模糊匹配两个接口。相较于关键词直接匹配，HITS优化排序算法考虑文章之间的全局信息，利用文章向量进行关联度计算，考虑到了关键词匹配算法所忽视的文章内容；而模糊匹配算法通过匹配查询词的相似词，进一步考虑到了语言的多样性，为匹配算法提供了更多的自由度和灵活性。

## 文件结构

```python
TextSearch
    ├──── data
    │       ├──── all_cnews.csv         中文数据集
    │       └──── all_news.csv          英文数据集
    ├──── results
    |       ├──── logs
    |       |       ├──── result.log    结果日志
    |       |       └──── server.log    服务器运行日志
    |       └──── visualize             可视化结果
    ├──── server_files
    |       ├──── news                  txt格式文档
    |       ├──── file_feats_100.npy    文档特征（1000维）
    |       ├──── similarity.npy        文档相似度矩阵
    |       ├──── synonym.json          相似词词表
    |       ├──── vocab.csv             文档词表
    |       └──── word_vec.npy          词向量矩阵
    ├──── user_files                    用户文件
    ├──── utils
    │       ├──── io_util.py            io功能函数
    │       └─── util.py                功能函数
    ├──── analysis.ipynb                结果分析、可视化
    ├──── config.yml                    配置、参数文件
    ├──── GUI.py                        客户端
    ├──── ipynb_importer.py     
    ├──── local_server.py               服务器端
    └──── preprocess.ipynb              数据预处理
```

## Quick Start

1. 下载TextSearch文件夹中全部文件（`server_files`文件夹可选）
2. 若未安装`server_files`文件夹，则需手动运行`preprocess.ipynb`中缺少的文件对应的cell
3. 运行如下指令启动服务器端

   ```shell
   python local_server.py
   ```

4. 运行如下指令启动客户端，使用GUI界面进行交互

   ```shell
   python GUI.py
   ```
