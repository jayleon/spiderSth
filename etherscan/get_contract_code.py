#!/usr/bin/python
# coding:utf-8
# 从etherscan.io获取contract_code信息

import sys,re
import logging,traceback
import lxml.etree as etree
import HTMLParser
from logging.handlers import TimedRotatingFileHandler

sys.path.append('../utils')
from mongo_utils import *
from http_utils import *
from common_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/get_contract_code.log'
logger = logging.getLogger('get_contract_code.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)


log_files = ''  # 日志目录
def Write_log(line):
    tm = time.localtime(time.time())
    now = time.strftime("%Y%m%d%H%M%S", tm)
    today = time.strftime("%Y%m%d", tm)
    log_file = os.path.join(log_files, ('get_contract_code.%s' % today))
    try:
        of = open(log_file, 'a+')
        of.write("%s\n" % (line))
        of.flush()
        of.close()
    except:
        print ("open %s failed" % log_file)

def to_etherscan(tokens):
    try:
        contractAddress = tokens['contractAddress']
        URL = "https://etherscan.io/address/%s#code" % contractAddress
        http = HttpRequest()
        http.setTimeout(50)
        texts = http.setUrl(URL).setRequestType('get').getResponse().text
        if texts != None:
            # xpath解析html源码
            html_parser = HTMLParser.HTMLParser()
            html_text = html_parser.unescape(texts)
            html = etree.HTML(html_text)

            editor_ = html.xpath('//*[@id="editor"]//text()')
            if editor_:
                csc = ''
                for value in editor_: csc += value.strip()
                if csc:
                    print csc
                    tokens['contractSourceCode'] = str(csc)
            else:
                editor_ = html.xpath('//*[@id="dividcode"]/pre[1]//text()')
                if editor_:
                    csc = ''
                    for value in editor_: csc += value.strip()
                    if csc:
                        print csc
                        tokens['contractSourceCode'] = str(csc)

            copytextarea2 = html.xpath('//*[@id="js-copytextarea2"]//text()')
            if copytextarea2:
                contractABI = copytextarea2[0].strip()
                print contractABI
                tokens['contractABI'] = contractABI

            verifiedbytecode2 = html.xpath('//*[@id="verifiedbytecode2"]//text()')
            if verifiedbytecode2:
                contractCreationCode = verifiedbytecode2[0].strip()
                print contractCreationCode
                tokens['contractCreationCode'] = contractCreationCode

            dividcode2 = html.xpath('//*[@id="dividcode"]/pre[2]//text()')
            if dividcode2:
                constructorArguments = ''
                for value in dividcode2: constructorArguments += value.strip()
                print constructorArguments
                if str(constructorArguments).find('bzzr') == -1:
                    tokens['constructorArguments'] = constructorArguments
        else:
            Write_log(contractAddress)
    except Exception, e:
        logger.error(e.message)
        logger.error(traceback.format_exc())
        Write_log(contractAddress)
    return tokens

def to_etherscan_getopcode(tokens):
    try:
        contractAddress = tokens['contractAddress']
        URL = "https://etherscan.io/api?module=opcode&action=getopcode&address=%s" % contractAddress
        http = HttpRequest()
        http.setTimeout(50)
        texts = http.setUrl(URL).setRequestType('get').getResponse().text
        if texts != None:
            # 解析json源码
            jt = json.loads(texts, encoding='utf-8')
            result = jt.get("result")
            if result:
                contractCreationCode = str(result).replace('<br>', '\r\n')
                print contractCreationCode
                tokens['contractCreationCode'] = contractCreationCode

        else:
            Write_log(contractAddress)
    except Exception, e:
        logger.error(e.message)
        logger.error(traceback.format_exc())
        Write_log(contractAddress)
    return tokens

def start():
    # 连接MongoDB，查询tokens，根据contractAddress到etherscan查询最新数据
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    for tokens in collection.find({"contractAddress": {"$gt": "0"}}, no_cursor_timeout=True).sort('contractAddress').batch_size(2):
        logger.info(tokens)
        tokens = to_etherscan_getopcode(tokens=tokens)
        collection.update_one({'contractAddress': tokens['contractAddress']}, {'$set': tokens})
        # break

def supplement():
    # 读取文件中的地址，重试抓取
    path = './normal_contract_code'
    normal_list = load_normal_list(path)
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    for addr in normal_list:
        tokens = collection.find_one({"contractAddress": addr})
        tokens = to_etherscan(tokens=tokens)
        collection.update_one({'contractAddress': tokens['contractAddress']}, {'$set': tokens})

if __name__ == '__main__':

    # 跑mongo中已有的数据
    #start()

    # 补充错误数据
    supplement()
    # logger.info("info msg...")