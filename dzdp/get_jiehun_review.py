#!/usr/bin/python
# coding:utf-8
# 从http://www.dianping.com获取结婚-婚纱摄影店铺的所有评论信息（已放弃）
# 评论中的部分汉字是以图片的形式出现的，需要经过图片识别转汉字后，根据html源码中的图片标识跟汉字做对应
# 美团汉字字典图片地址：http://s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/6067cf4feaf08658ff6777eea9d362b0.svg

import sys,re
import logging,traceback
import lxml.etree as etree
import HTMLParser

sys.path.append('../utils')
from common_utils import *
from http_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger('get_jiehun_review.py')

ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

def crawler_it(ids, number):
    url = 'http://www.dianping.com%s/review_all/p%s' % (ids, number)
    http = HttpRequest()
    http.setTimeout(10)
    headerDict = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control":"max-age=0",
        "Connection":"keep-alive",
        "Accept-Encoding":"gzip, deflate",
        "Host":"www.dianping.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
    }
    http.setHeader(headerDict=headerDict)
    cookies = {
        "cityid": "2",
        "_lxsdk_cuid": "16657b22265c8-045ac4ffe61641-346f7808-13c680-16657b22265c8",
        "_lxsdk": "16657b22265c8-045ac4ffe61641-346f7808-13c680-16657b22265c8",
        "baidusearch_ab": "citybranch%3AA%3A1%7Cshop%3AA%3A1",
        "dper": "29b422e3c6041c2397227530b26357fc4036c88e553ad2d87722b74e959b6deab1ffa2d5b152113415eddd3d09ae55e3c563bc248b3b70e9e919cdfc079b1c34baa9c4a9d20bad9d252ebc41751d4ce9ee1c49b00521354549d7330d48de5f96",
        "ll": "7fd06e815b796be3df069dec7836c3df",
        "ua": "dpuser_7873345227",
        "ctu": "55a99c85fad08a99d4daa3dac2a3db4b2f8841967992518800f22f685af25aed",
        "uamo": "13800138000",
        "cy": "2",
        "cye": "beijing",
        "aburl": "1",
        "Hm_lvt_dbeeb675516927da776beeb1d9802bd4": "1539079999",
        "QRCodeBottomSlide": "hasShown",
        "wed_user_path": "163|0",
        "Hm_lpvt_dbeeb675516927da776beeb1d9802bd4": "1539079999"
    }
    http.setCookies(cookies=cookies)
    texts = http.setUrl(url).setRequestType('get').getResponse().text
    if texts != None:
        # xpath解析html源码
        html_parser = HTMLParser.HTMLParser()
        html_text = html_parser.unescape(texts)
        html = etree.HTML(html_text)

        symbols = html.xpath('//*[@id="review-list"]/div[2]/div[1]/div[3]/div[3]/ul/li/div/div[4]/text()')
        if symbols:
            for value in symbols:
                print value.strip()


def start():
    # 读取所有种子链接
    path = './normal_urls'
    normal_list = load_normal_list(path)
    # 抓取任务进队列
    crawler_it(normal_list, 1)


if __name__ == '__main__':
    # start()
    crawler_it('/shop/76858126', 1)