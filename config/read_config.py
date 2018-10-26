#!/usr/bin/python
# coding:utf-8

"""
@Time: 2018/10/25 下午7:27
@Author: leon
@File: read_config.py
@Software: PyCharm Community Edition
"""

import os, sys
import ConfigParser
sys.path.append('../utils')
from common_utils import *

# 获取文件的当前路径（绝对路径）
cur_path = os.path.dirname(os.path.realpath(__file__))

# 获取config.ini的路径
config_path = os.path.join(cur_path, 'config_dev.ini')
# config_path = os.path.join(cur_path, 'config_test.ini')
# config_path = os.path.join(cur_path, 'config_production.ini')

conf = ConfigParser.ConfigParser()
conf.read(config_path)

# mongo
mongo_prop = conf.get('mongo', 'mongo_prop')

# mysql
mysql_host = conf.get('mysql', 'mysql_host')

# redis
redis_nodes = conf.get('redis', 'redis_nodes')

# es
es_host = conf.get('es', 'es_host')
es_port = conf.get('es', 'es_port')

# email
mailto_list = conf.get('email', 'mailto_list')
mail_host = conf.get('email', 'mail_host')
mail_user = conf.get('email', 'mail_user')
mail_pass = conf.get('email', 'mail_pass')

# hdfs
hdfs_host = conf.get('hdfs', 'hdfs_host')

# restful
restful_url = conf.get('restful', 'restful_url')

# rpc
rpc_url = conf.get('rpc', 'rpc_url')

# 获取proxy_ips的路径
proxy_ips_path = os.path.join(cur_path, 'proxy_ips')
proxy_ips = load_normal_list(proxy_ips_path)