#!/usr/bin/python
# coding:utf-8
# mongodb集群工具类

import pymongo
import time, os, sys, logging

logger = logging.getLogger('mongo_utils.py')

ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

# redis集群
class MongoCluster:
    def connect(self):
        return pymongo.MongoClient('mongodb://username:password@127.0.0.1:27019,127.0.0.2:27019,127.0.0.3:27019')


if __name__ == "__main__":
    client = MongoCluster().connect()
    db = client.get_database('mydatabase')
    collection = db.get_collection('mytable')
    for result in collection.find({"contractAddress":{"$gt":"0"}}).sort('contractAddress'):
        print result
        print result['_id']
        break