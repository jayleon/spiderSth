#!/usr/bin/python
# coding:utf-8
# mongodb集群工具类

import pymongo
import time, os, sys, logging
from logging.handlers import TimedRotatingFileHandler
sys.path.append('../config')
import read_config


log_file_path = '../log/mongo_utils.log'
logger = logging.getLogger('mongo_utils.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

# redis集群
class MongoCluster:
    def connect(self):
        return pymongo.MongoClient('mongodb://%s' % read_config.mongo_prop)


if __name__ == "__main__":
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    for result in collection.find({"contractAddress":"0xef1878ace027089520e8825bbdd16ad0048e3288"}):
        print result
        print result['_id']
        break