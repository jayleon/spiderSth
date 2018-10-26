#!/usr/bin/python
# coding:utf-8
# 从hdfs读取文件到mongo；本地HdfsClient.open报错，上传脚本到服务器上执行OK。

import sys,re
import logging,traceback
import lxml.etree as etree
import HTMLParser
from logging.handlers import TimedRotatingFileHandler

sys.path.append('../utils')
from mongo_utils import *
from common_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/hdfs2mongo.log'
logger = logging.getLogger('hdfs2mongo.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

hdfs_ip = 'ip-192-168-0-145.ap-southeast-1.compute.internal'

log_files = ''  # 日志目录
def Write_log(line):
    tm = time.localtime(time.time())
    now = time.strftime("%Y%m%d%H%M%S", tm)
    today = time.strftime("%Y%m%d", tm)
    log_file = os.path.join(log_files, ('hdfs2mongo.%s' % today))
    try:
        of = open(log_file, 'a+')
        of.write("%s\n" % (line))
        of.flush()
        of.close()
    except:
        print ("open %s failed" % log_file)

def start():
    # 连接MongoDB，查询tokens，根据contractAddress到etherscan查询最新数据
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('mrout_6000001-6001000')
    # collection.insert_one()

    # 连接HDFS读取文件
    from pyhdfs import HdfsClient
    client2 = HdfsClient(hosts='%s,50070' % hdfs_ip, max_tries=10)
    # 返回这个用户的根目录
    print client2.get_home_directory()
    # 返回可用的namenode节点
    print client2.get_active_namenode()
    # 返回指定目录下的所有文件
    print client2.listdir("/user/leon/mrout_3_6000001-6001000/")
    # 读某个文件
    client2.mkdirs("/user/leon")
    inputfile = client2.open('/user/leon/mrout_3_6000001-6001000/part-00000')
    # 查看文件内容
    for r in inputfile:
        line = str(r).encode('utf-8')  # open后是二进制,str()转换为字符串并转码
        print(line)
        # break

if __name__ == '__main__':

    # 读hdfs某个目录下所有文件存入mongo
    start()
