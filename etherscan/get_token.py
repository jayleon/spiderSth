#!/usr/bin/python
# coding:utf-8
# 从etherscan.io获取token信息

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

log_file_path = '../log/get_token.log'
logger = logging.getLogger('get_token.py')
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
    log_file = os.path.join(log_files, ('get_token.%s' % today))
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
        URL = "https://etherscan.io/token/%s" % contractAddress
        http = HttpRequest()
        http.setTimeout(50)
        texts = http.setUrl(URL).setRequestType('get').getResponse().text
        if texts != None:
            # xpath解析html源码
            html_parser = HTMLParser.HTMLParser()
            html_text = html_parser.unescape(texts)
            html = etree.HTML(html_text)

            symbols = html.xpath('/html/head/title//text()')
            if symbols:
                symbol = ''
                for value in symbols: symbol += value.strip()
                symbol_ = re.search('\(.*?\)', symbol)
                if symbol_:
                    symbol = symbol_.group().strip().replace('(', '').replace(')', '')
                    print symbol
                    tokens['symbol'] = str(symbol)

            fullNames = html.xpath('//*[@id="address"]//text()')
            if fullNames:
                fullName = fullNames[0].strip()
                print fullName
                tokens['fullName'] = fullName

            totals = html.xpath('//*[@id="ContentPlaceHolder1_divSummary"]/div[1]/table/tr[1]/td[2]//text()')

            if totals:
                total = ''
                for value in totals: total += value.strip()
                # 正则匹配所需值
                total1 = total.split(' ')[0].replace(',', '')
                print total1
                tokens['totalSupply1'] = total1
                total2s = re.search('\(\$.*?\)', total)
                if total2s:
                    total2 = total2s.group().strip().replace('($', '').replace(')', '').replace(',', '')
                    print total2
                    tokens['totalSupply2'] = total2
            prices = html.xpath('//*[@id="ContentPlaceHolder1_tr_valuepertoken"]/td[2]//text()')
            if prices:
                price = ''
                for value in prices: price += value.strip()
                # 正则匹配所需值
                price1s = re.search('\$.*?\@', price)
                if price1s:
                    price1 = price1s.group().strip().replace('$', '').replace('@', '').replace(',', '').replace(' ', '')
                    print price1
                    tokens['priceUsd'] = price1

                price2s = re.search('\@ .*? ', price)
                if price2s:
                    price2 = price2s.group().strip().replace('@', '').replace(',', '').replace(' ', '')
                    print price2
                    tokens['priceEth'] = price2

            holders = html.xpath('//*[@id="ContentPlaceHolder1_tr_tokenHolders"]/td[2]//text()')
            if holders:
                holder = ''
                for value in holders: holder += value.strip()
                holder = holder.replace('addresses', '').replace(',', '').replace(' ', '')
                print holder
                tokens['holders'] = holder
            decimals = html.xpath('//*[@id="ContentPlaceHolder1_trDecimals"]/td[2]//text()')
            if decimals:
                decimal = ''
                for value in decimals: decimal += value.strip()
                decimal = decimal.replace(',', '').replace(' ', '')
                print decimal
                tokens['decimals'] = decimal
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
    for tokens in collection.find({"contractAddress": {"$gt": "0"}}).sort('contractAddress'):
        logger.info(tokens)
        tokens = to_etherscan(tokens=tokens)
        collection.update_one({'contractAddress': tokens['contractAddress']}, {'$set': tokens})
        # break

def supplement():
    # 读取文件中的地址，重试抓取
    path = './normal_tokens'
    normal_list = load_normal_list(path)
    client = MongoCluster().connect()
    db = client.get_database('gse-transaction')
    collection = db.get_collection('tokens')
    for addr in normal_list:
        tokens = collection.find_one({"contractAddress": addr})
        tokens = to_etherscan(tokens=tokens)
        collection.update_one({'contractAddress': tokens['contractAddress']}, {'$set': tokens})

if __name__ == '__main__':
    supplement()
    logger.info("info msg...")