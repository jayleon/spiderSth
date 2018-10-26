#!/usr/bin/python
# coding:utf-8
# redis集群工具类

from rediscluster import StrictRedisCluster
import json, os, sys, logging
from logging.handlers import TimedRotatingFileHandler
sys.path.append('../config')
import read_config

log_file_path = '../log/redis_utils.log'
logger = logging.getLogger('redis_utils.py')
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
class RedisCluster:

    def connect(self):
        rn = read_config.redis_nodes
        redis_nodes = json.loads(rn)
        return StrictRedisCluster(startup_nodes=redis_nodes, decode_responses=True)

if __name__ == "__main__":
    rs = RedisCluster().connect()
    rs.set('a', 'a_value')

    print rs.get('a')