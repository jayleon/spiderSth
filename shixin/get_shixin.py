#!/usr/bin/python
# coding:utf-8
# 以百度为入口，获取全国法院失信被执行人名单，百度做了反扒，每天可获取数据有限；

import logging
import sys, json, time, hashlib
import traceback
from logging.handlers import TimedRotatingFileHandler

from elasticsearch import Elasticsearch

sys.path.append('../utils')
from http_utils import *
from common_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/get_shixin.log'
logger = logging.getLogger('get_shixin.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

class shixin():
    # 设置name
    logger.info("get shixin begin...")

    ES = Elasticsearch([{'host': '127.0.0.1', 'port': 9200}])
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Host": "sp0.baidu.com",
        "Referer":"https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&ch=&tn=baiduerr&bar=&wd=%E5%A4%B1%E4%BF%A1"
    }

    # 编写爬取方法
    def doit(self, url, page):
        try:
            # 当前页若有20个URL均抓取过，则退出。
            # rs = RedisUtil(None, None, REDIS_DB_0, None)

            http = HttpRequest()
            http.setTimeout(5)
            html_page = http.setUrl(url).setHeader(self.headers).setRequestType('get').getResponse().text
            # html_page = ''
            logger.info("shixin parse begin...page===%s" % page)

            logger.info("shixin parse ...body size===%s===url===%s" % (len(html_page), url))
            # logger.info(response.body)
            if html_page != None and html_page.find('"status":"0"') != -1:
                box = html_page.replace('/**/jQuery1102006994179472827677_1539829531930(', '').replace(');', '')
                try:
                    if box:
                        url_ = json.loads(box)
                        logger.info('url_-------%s' % url_['data'][0]['result'][0])
                        for data in url_['data'][0]['result']:

                            datas = {}
                            # 数据入ES
                            mtime = int(time.time())
                            now_tm = time.localtime(mtime)
                            now = time.strftime("%Y-%m-%d %H:%M:%S", now_tm)
                            datas["timestamp"] = mtime
                            datas["@timestamp"] = now
                            # datas["gistId"] = '11111'
                            # print type(data)
                            for key, value in data.items():
                                # print key,value
                                # print type(key),type(value)
                                if key[0] == '_':
                                    continue
                                datas[key.encode("utf-8")] = str(value)
                            if datas["gistId"]:
                                m2 = hashlib.md5()
                                m2.update(str(datas["gistId"]))
                                url_md5 = m2.hexdigest()
                                # json.dumps()
                                self.ES.index(index='shixin_info', doc_type='shixin_type', id=url_md5, body=datas)
                            logger.info("shixin success...url===%s" % url)
                            # yield item

                except Exception, e:
                    logger.error(traceback.format_exc())

            else:
                logger.info("shixin end...url===%s" % url)

        except Exception, e:
            logger.error(traceback.format_exc())


def start():
    page = 10
    url = u'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=6899&query=%E5%85%A8%E5%9B%BD%E6%B3%95%E9%99%A2%E5%A4%B1%E4%BF%A1%E8%A2%AB%E6%89%A7%E8%A1%8C%E4%BA%BA%E5%90%8D%E5%8D%95&pn=30&rn=10&ie=utf-8&oe=utf-8&format=json&t=1539829555013&cb=jQuery1102006994179472827677_1539829531930&_=1539829531934'
    for i in range(1000):
        dopage = page + (i - 1) * 10
        dourl = url.replace('&pn=%s' % page, '&pn=%s' % dopage)
        shixin().doit(dourl, dopage)

if __name__ == '__main__':

    while True:
        start()
        time.sleep(3600*24)