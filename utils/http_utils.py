#!/usr/bin/env python
# coding:utf-8
# http请求工具类

import base64
import datetime
import StringIO, gzip
import time, sys

import logging
import requests
import urllib3
import lxml.etree as etree
import HTMLParser

reload(sys)
sys.setdefaultencoding('utf-8')

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger('http_utils.py')

ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

class HttpRequest(object):
    """http 请求类，支持get or post
       可以设置header，进行gzip压缩或解压缩
    """
    cookies = None
    response_header = {}

    def __init__(self, url=None, requestType='post', timeout=3, headerDict={}):
        self.url = url
        self.type = requestType
        self.body = {}
        self.timeout = timeout
        self.headerDict = headerDict
        self.cookies = None

    def setUrl(self, url):
        self.url = url
        return self

    def getUrl(self):
        return self.url

    def setRequestType(self, requestType):
        self.type = requestType
        return self

    def getRequestType(self):
        return self.requestType

    def setBody(self, body):
        self.body = body
        return self

    def getBody(self):
        return self.body

    def getResponse(self):
        return self.fire()

    def post(self):
        if not self.url:
            raise Exception('url must not empty !')
        self.setRequestType('post')
        return self.send()

    def get(self):
        if not self.url:
            raise Exception('url must not empty!')

        self.setRequestType('get')
        return self.send()

    def put(self):
        if not self.url:
            raise Exception('url must not empty!')
        self.setRequestType('put')
        return self.send()

    def setHeader(self, headerDict):
        """设置请求头"""
        self.headerDict = headerDict
        return self

    def send(self):
        try:
            res = self.getResponse()
            while True:
                if res is None:
                    logger.info('访问资源超时：%s' % self.url)
                    return None
                elif res.status_code == 503:
                    return None
                elif res.status_code == 429:
                    time.sleep(0.3)
                    res = self.fire()
                else:
                    break

            if self.headerDict.get('Accept-Encoding', None) == 'gzip':
                compressedstream = StringIO.StringIO(res)
                gziper = gzip.GzipFile(fileobj=compressedstream)
                res = gziper.read()
            response = res.content.decode(res.apparent_encoding)
            return response
        except Exception, e:
            logger.error(e)
            return None

    def fire(self):
        proxies = None

        logger.info('local ip !!')
        try:
            if self.type == 'post':
                response = requests.post(self.url, data=self.body, headers=self.headerDict, timeout=self.timeout,
                                         proxies=proxies, cookies=self.cookies)
                logger.info('request_type:post, url:%s, status_code:%s' % (self.url, response.status_code))
            elif self.type == 'put':
                response = requests.put(self.url, data=self.body, headers=self.headerDict, timeout=self.timeout,
                                        proxies=proxies, cookies=self.cookies)
                logger.info('request_type:put, url:%s, status_code:%s' % (self.url, response.status_code))
            else:
                response = requests.get(self.url, headers=self.headerDict, timeout=self.timeout, proxies=proxies,
                                        cookies=self.cookies, data=self.body, verify=False)
                logger.info('request_type:get,  url:%s, status_code:%s' % (self.url, response.status_code))
            self.cookies = response.cookies
            self.response_header = response.headers
            return response
        except Exception, e:
            logger.error('error_url:%s,error_message:%s' % (self.url, e))
            return None

    def getResponseHeader(self):
        return self.response_header

    def getCookies(self):
        return self.cookies

    def setCookies(self, cookies):
        self.cookies = cookies

    def getDate(self):
        """获取当前时间"""
        return datetime.datetime.now().strftime('%Y-%m-%d')

    def setTimeout(self, timeout):
        """超时设置"""
        self.timeout = timeout

    def encrypt(self, encryptFields=[]):
        """指定加密字段"""
        for field in encryptFields:
            if field not in self.body.keys():
                raise Exception('encrypt field %s not exists!' % field)
            self.body[field] = self.__encrypt(self.body[field])
        return self

    def __encrypt(self, data):
        """具体加密逻辑 """
        # 此处代码隐藏
        return base64.b64encode(data)


__all__ = ['HttpRequest']

if __name__ == '__main__':
    import re
    URL = "https://etherscan.io/token/0x0343be93499e11ac3e2ec0b7dafb66dc1b6b0eb9"
    http = HttpRequest()
    http.setTimeout(10)
    header = {
        'accept-encoding': 'gzip, deflate, br'
    }
    texts = http.setUrl(URL).setRequestType('get').getResponse().text
    # xpath解析html源码
    html_parser = HTMLParser.HTMLParser()
    html_text = html_parser.unescape(texts)
    html = etree.HTML(html_text)
    # print texts
    symbols = html.xpath('/html/head/title/text()')
    if symbols:
        symbol = ''
        for value in symbols: symbol += value.strip()
        symbol_ = re.search('\(.*?\)', symbol)
        if symbol_:
            symbol = symbol_.group().strip().replace('(', '').replace(')', '')
            print symbol

    fullNames = html.xpath('//*[@id="address"]/text()')
    if fullNames:
        fullName = fullNames[0].strip()
        print fullName

    totals = html.xpath('//*[@id="ContentPlaceHolder1_divSummary"]/div[1]/table/tr[1]/td[2]/text()')

    if totals:
        total = ''
        for value in totals: total += value.strip()
        # 正则匹配所需值
        total1 = total.split(' ')[0].replace(',', '')
        print total1
        total2s = re.search('\(\$.*?\)', total)
        if total2s:
            total2 = total2s.group().strip().replace('($', '').replace(')', '').replace(',', '')
            print total2
    prices = html.xpath('//*[@id="ContentPlaceHolder1_tr_valuepertoken"]/td[2]/text()')
    if prices:
        price = ''
        for value in prices: price += value.strip()
        # 正则匹配所需值
        price1s = re.search('\$.*?\@', price)
        if price1s:
            price1 = price1s.group().strip().replace('$', '').replace('@', '').replace(',', '').replace(' ', '')
            print price1

        price2s = re.search('\@ .*? ', price)
        if price2s:
            price2 = price2s.group().strip().replace('@', '').replace(',', '').replace(' ', '')
            print price2

    holders = html.xpath('//*[@id="ContentPlaceHolder1_tr_tokenHolders"]/td[2]/text()')
    if holders:
        holder = ''
        for value in holders: holder += value.strip()
        holder = holder.replace('addresses', '').replace(',', '').replace(' ', '')
        print holder
    decimals = html.xpath('//*[@id="ContentPlaceHolder1_trDecimals"]/td[2]/text()')
    if decimals:
        decimal = ''
        for value in decimals: decimal += value.strip()
        decimal = decimal.replace(',', '').replace(' ', '')
        print decimal