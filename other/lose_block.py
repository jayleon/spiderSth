#!/usr/bin/python
# coding:utf-8

"""
@Time: 2018/11/2 上午11:16
@Author: leon
@File: lose_block.py
@Software: PyCharm Community Edition
# scp other/lose_block.py root@172.0.0.1:/data/leon/python/other/
# nohup python lose_block.py > /dev/null 2>&1  &
"""

import sys,datetime

sys.path.append('../utils')
from mongo_utils import *
from read_config import *
from common_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/lose_block.log'
logger = logging.getLogger('lose_block.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

def start():
    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('block')
    collection2 = db.get_collection('lose_block')
    insertlist = []
    for i in xrange(1, 6500001):
        isok = False
        for numbers in collection.find({"number": i}, {"number": 1}, no_cursor_timeout=True).batch_size(1):
            isok = True
            insertlist.append({"blockNum": numbers['number'], "hasMongo": 1, "hasHdfs": 0})
            break
        if not isok:
            insertlist.append({"blockNum": i, "hasMongo": 0, "hasHdfs": 0})
        if len(insertlist) >= 100:
            collection2.insert_many(insertlist)
            insertlist = []

    if len(insertlist) > 0:
        collection2.insert_many(insertlist)


def repetition():
    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('block')
    collection2 = db.get_collection('lose_block')
    for i in xrange(1, 6500001):
        logger.info("now is %s"% i)
        bsize = collection.find({"number": i}, {"number": 1}, no_cursor_timeout=True).count()
        if bsize > 1:
            logger.info("now is %s ;repetition size is:%s" % (i, bsize))
            collection2.update_one({'blockNum': i}, {'$set': {"repetition": bsize}})

def createIndex():
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    for i in xrange(0, 200):
        i = 1
        collection = db.get_collection('hash_block_%s' % i)
        collection.create_index([('transaction', 1)])
        break

def transLoseBlock(from_no, to_no):
    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('transactions_%s-%s' % (from_no, to_no))
    collection2 = db.get_collection('transactions_%s-%s_lose_block' % (from_no, to_no))
    for i in xrange(from_no, to_no + 1):
        logger.info("now is %s" % i)
        bsize = collection.find({"blockNumber": i}, {"blockNumber": 1}, no_cursor_timeout=True).count()
        if bsize < 1:
            logger.info("now is %s ;repetition size is:%s" % (i, bsize))
            collection2.insert_one({'blockNum': i, 'hasMongo': 0, 'hasHdfs': 0})

def checkFile():
    listall = []
    list1 = getFile2List('losetr_6000001-6100000')
    listall.extend(list1)
    list2 = getFile2List('losetr_6100001-6200000')
    listall.extend(list2)
    list3 = getFile2List('losetr_6200001-6300000')
    listall.extend(list3)
    list4 = getFile2List('losetr_6300001-6400000')
    listall.extend(list4)
    list5 = getFile2List('losetr_6400001-6500000')
    listall.extend(list5)
    print len(listall)

    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('transactions_6000001-6500000_lose_block')
    listall2 = []

    # 第一个{} 放where条件 第二个{} 指定那些列显示和不显示 （0表示不显示 1表示显示)
    # collection.find({},{"blockNum":1,"_id":0},no_cursor_timeout=True);
    for numbers in collection.find(no_cursor_timeout=True).batch_size(1):
        if numbers:
            listall2.append(str(numbers['blockNum']))
    print len(listall2)

    f = open('./checkfile', 'w')
    numbers_ = []
    for number in listall2:
        if number not in listall:
            numbers_.append(number)
            if len(numbers_) >= 10:
                ss = ','.join('%s' % id for id in numbers_)
                f.write('%s\n' % ss)
                numbers_ = []
    if len(numbers_) > 0:
        ss = ','.join('%s' % id for id in numbers_)
        f.write('%s\n' % ss)
    f.close()

def getFile2List(path):
    list = []
    list1 = load_normal_list(path)
    for nums in list1:
        nums_ = str(nums).split(',')
        for num in nums_:
            if num:
                # print num
                list.append(str(num))
    return list

def gseTrans(from_no, to_no):
    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('transactions_%s-%s' % (from_no, to_no))
    collection2 = db.get_collection('gse-transactions')
    count = 1
    for trans in collection.find({"contractAddress":"0xe530441f4f73bdb6dc2fa5af7c3fc5fd551ec838"}, {"_id": 0},
                                 no_cursor_timeout=True).sort("timestamp").batch_size(1):
        logger.info("gseTrans now timestamp is %s" % trans['timestamp'])
        collection2.insert_one(trans)
        count = count + 1
    logger.info("gseTrans success count is %s" % count)

def getMongo2Csv():

    csvName = './gse-transactions-0915.csv'
    csvfile = file(csvName, 'ab')
    csvfile.write(codecs.BOM_UTF8)
    writer = csv.writer(csvfile)

    # 连接MongoDB
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('gse-transactions')
    for trans in collection.find({"timestamp":{"$gt":1536940800}}, {"_id": 0},
                                 no_cursor_timeout=True).batch_size(1):
        logger.info("gseTrans now timestamp is %s" % trans['timestamp'])
        resultdata = []
        if 'from' in trans:
            resultdata.append(str(trans['from']).replace('000000000000000000000000', ''))
        else:
            resultdata.append('')
        if 'to' in trans:
            resultdata.append(str(trans['to']).replace('000000000000000000000000', ''))
        else:
            resultdata.append('')
        if 'value' in trans:
            resultdata.append(str(trans['value']))
        else:
            resultdata.append('')
        if 'symbol' in trans:
            resultdata.append(str(trans['symbol']))
        else:
            resultdata.append('')
        if 'contractAddress' in trans:
            resultdata.append(str(trans['contractAddress']))
        else:
            resultdata.append('')
        if 'blockNumber' in trans:
            resultdata.append(str(trans['blockNumber']))
        else:
            resultdata.append('')
        if 'hash' in trans:
            resultdata.append(str(trans['hash']))
        else:
            resultdata.append('')
        if 'gas' in trans:
            resultdata.append(str(trans['gas']))
        else:
            resultdata.append('')
        if 'gasPrice' in trans:
            resultdata.append(str(trans['gasPrice']))
        else:
            resultdata.append('')
        if 'gasUsed' in trans:
            resultdata.append(str(trans['gasUsed']))
        else:
            resultdata.append('')
        if 'timestamp' in trans:
            resultdata.append(parse_time(trans['timestamp']))
        else:
            resultdata.append('')
        writer.writerow(resultdata)

    csvfile.close()

if __name__ == "__main__":
    # 查询块中丢失的块，存入指定表
    # start()

    # 查询块中重复的块记录，存入指定表
    # repetition()

    # 批量表建索引
    # createIndex()

    # 查询交易中丢失的块，存入指定表
    # transLoseBlock(5500001, 6000000)

    # 比对文件
    # checkFile()

    # 将GSE的交易根据合约地址查出来，存入单独的交易表
    # gseTrans(6000001, 6500000)

    # 从Mongo导出csv文件
    getMongo2Csv()