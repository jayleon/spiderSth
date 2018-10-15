#!/usr/bin/python
# coding:utf-8
# redis集群工具类

from rediscluster import StrictRedisCluster
import time, os, sys, logging

logger = logging.getLogger('redis_utils.py')

ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

# redis集群
class RedisCluster:

    def connect(self):
        redis_nodes = [{'host': '127.0.0.1', 'port': 7001},
                       {'host': '127.0.0.1', 'port': 7002},
                       {'host': '127.0.0.2', 'port': 7003},
                       {'host': '127.0.0.2', 'port': 7004},
                       {'host': '127.0.0.3', 'port': 7005},
                       {'host': '127.0.0.3', 'port': 7006}
                       ]
        return StrictRedisCluster(startup_nodes=redis_nodes, decode_responses=True)

if __name__ == "__main__":
    rs = RedisCluster().connect()
    rs.set('a', 'a_value')

    print rs.get('a')