import logging
import logging.handlers
import yaml
import pandas as pd
import numpy as np
import json


def init_logger(log_path, logging_name=''):
    logger = logging.getLogger(logging_name)
    logger.setLevel(level=logging.DEBUG)
    handler = logging.FileHandler(log_path, encoding='UTF-8')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(console)
    return logger


def write_log(log, info, verbose=False):
    log.info(info)
    # if verbose:
    #     print(info)


def load_yaml(file_path, verbose=True):
    with open(file_path, "r") as f:
        yml_file = yaml.load(f, Loader=yaml.SafeLoader)
    if verbose:
        print("Load yaml file from {}".format(file_path))
    return yml_file


def load_csv(path):
    return pd.read_csv(path)


def load_npy(path):
    return np.load(path, allow_pickle=True)


def load_json(path):
    with open(path, "r") as f:
        jsonfile = json.load(f)
    return jsonfile


def dump_json(item):
    return json.dumps(item)


def send_txt(path, conn):
    with open(path, 'rb') as f:
        data = f.read()
        conn.sendall(data)
        f.close()
