#!/usr/bin/python
# coding:utf-8
# 多线程，调Restful服务获取contract_code信息

import sys,re
import logging,traceback
import threading

from Queue import Queue

sys.path.append('../utils')
from mongo_utils import *
from http_utils import *
from common_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/get_contract_code_thread.log'
logger = logging.getLogger('get_contract_code_thread.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

contract_queue = Queue()  # 队列

log_files = ''  # 日志目录
def Write_log(line):
    tm = time.localtime(time.time())
    now = time.strftime("%Y%m%d%H%M%S", tm)
    today = time.strftime("%Y%m%d", tm)
    log_file = os.path.join(log_files, ('get_contract_code_thread.%s' % today))
    try:
        of = open(log_file, 'a+')
        of.write("%s\n" % (line))
        of.flush()
        of.close()
    except:
        print ("open %s failed" % log_file)

class to_restful_getcode(threading.Thread):
    def run(self):
        try:
            global contract_queue
            client = MongoCluster().connect()
            db = client.get_database('gse-transaction')
            collection = db.get_collection('tokens')
            while not contract_queue.empty():
                print contract_queue.qsize()
                tokens = contract_queue.get(block=False)
                if not tokens:
                    break
                contractAddress = tokens['contractAddress']
                URL = "http://localhost:9090/usertoken/getTokenInfo?contractAddress=%s" % contractAddress
                http = HttpRequest()
                header = {"Accept": "application/json"}
                http.setHeader(headerDict=header)
                http.setTimeout(50)
                texts = http.setUrl(URL).setRequestType('get').getResponse().text
                if texts != None:
                    result_ = json.loads(texts)
                    if str(result_['errorCode']) == '0':
                        object_ = result_['object']
                        collection.update_one({'contractAddress': object_['contractAddress']}, {'$set': object_})
                    else:
                        Write_log(contractAddress)
                else:
                    Write_log(contractAddress)

        except Exception, e:
            logger.error(e.message)
            logger.error(traceback.format_exc())
            Write_log(contractAddress)

def start():
    # 连接MongoDB，查询tokens，根据contractAddress到etherscan查询最新数据
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    global contract_queue
    for tokens in collection.find({"contractAddress": {"$gt": "0"}}, {"contractAddress":1}, no_cursor_timeout=True).sort('contractAddress').batch_size(2):
        logger.info(tokens)
        contract_queue.put(tokens)

    # 任务开始
    for i in range(100):
        p = to_restful_getcode()
        p.start()

def supplement():
    # 读取文件中的地址，重试抓取
    path = './normal_contract_code_thread'
    normal_list = load_normal_list(path)
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    global contract_queue
    for addr in normal_list:
        tokens = collection.find_one({"contractAddress": addr}, {"contractAddress":1})
        print tokens
        if tokens:
            contract_queue.put(tokens)

    # 任务开始
    for i in range(100):
        p = to_restful_getcode()
        p.start()

if __name__ == '__main__':

    # 跑mongo中已有的数据
    # start()

    # 补充错误数据
    supplement()
