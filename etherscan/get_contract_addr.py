#!/usr/bin/python
# coding:utf-8
# 从rpc判断一个地址是否为合约地址；（result=0x，非合约地址）
# nohup python get_contract_addr.py > /dev/null 2>&1  &

import sys,re
import logging,traceback
import lxml.etree as etree
import HTMLParser
from logging.handlers import TimedRotatingFileHandler

sys.path.append('../utils')
from mongo_utils import *
from http_utils import *
from common_utils import *
from read_config import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/get_contract_addr.log'
logger = logging.getLogger('get_contract_addr.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

URL = read_config.rpc_url

log_files = ''  # 日志目录
def Write_log(line):
    tm = time.localtime(time.time())
    now = time.strftime("%Y%m%d%H%M%S", tm)
    today = time.strftime("%Y%m%d", tm)
    log_file = os.path.join(log_files, ('get_contract_addr.%s' % today))
    try:
        of = open(log_file, 'a+')
        of.write("%s\n" % (line))
        of.flush()
        of.close()
    except:
        print ("open %s failed" % log_file)

def to_rpc(addrs):
    try:
        addr = addrs['addr']
        # addr = '0xe530441f4f73bdb6dc2fa5af7c3fc5fd551ec838'

        http = HttpRequest()
        header = {"Content-Type":"application/json"}
        http.setHeader(headerDict=header)
        body = {"jsonrpc":"2.0","method":"eth_call","params":[{"data":"0x95d89b41","to":addr},"latest"],"id":1}
        http.setBody(body=json.dumps(body, ensure_ascii=False))
        http.setTimeout(50)
        texts = http.setUrl(URL).setRequestType('post').getResponse().text
        # print texts
        if texts != None and str(texts).find('error') == -1:
            result_ = json.loads(texts)
            if str(result_['result']) != '0x':
                return addr
        else:
            Write_log(addr)
    except Exception, e:
        logger.error(e.message)
        logger.error(traceback.format_exc())
        Write_log(addr)
    return ""

def start(addr):
    # 连接MongoDB，查询tokens，根据contractAddress到etherscan查询最新数据
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('transaction_addr')
    collection2 = db.get_collection('tokens')
    # 设置no_cursor_timeout = True，永不超时，游标连接不会主动关闭，需要手动关闭
    # 设置batch_size返回文档数，默认应该是101个文档或者size超过1M，可以设置小一些
    for addrs in collection.find({"addr": {"$gt": addr}}, no_cursor_timeout=True).batch_size(2):
        logger.info("now addr is:%s" % addrs['addr'])
        addr_ = to_rpc(addrs=addrs)
        if addr_:
            # mongoBD.tokens里判断此地址是否存在
            tokens = collection2.find_one({"contractAddress": addr_},{"contractAddress":1})
            if not tokens:
                collection2.insert_one({'contractAddress': addr_})
        # break

if __name__ == '__main__':

    # 跑mongo中已有的数据
    addr = '0'
    if len(sys.argv) > 1:
        addr = sys.argv[1]
    start(addr)
