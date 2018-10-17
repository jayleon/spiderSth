#!/usr/bin/python
# coding:utf-8
# 手机QQ APP扫描二维码登陆web QQ，抓取QQ基本信息和实时聊天文本记录；不包含表情和图片；
# 请求地址：http://localhost:7778/qqlogin
# ⚠ 注意：
# 1.手机QQ APP上会有web登录提示，请忽略，不做任何操作；
# 2.抓取期间会有登录超时情况，需查看报警日志或新增即时通讯报警方式；

import os, random, base64
import requests
import re
import json
import sys
import ssl
import threading
import execjs
from Queue import Queue

import tornado.web
from concurrent.futures import ThreadPoolExecutor

sys.path.append('../utils')
from http_utils import *
from es_utils import *

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/login_qq.log'
logger = logging.getLogger('login_qq.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')  # 存放登录二维码的位置，不需要改

es_queue = Queue()  # 入ES队列
http_queue = Queue()  # 推送数据队列

qrsig = ''
ptqrtoken = ''
uin = ''
ptwebqq = ''
psessionid = ''
vfwebqq = ''
ls_f = ''
groupNames = {}

global qq_msg
qq_msg = ''
global error_num
error_num = 0

class BaseHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(50)

# 扫码登陆入口
class web_QQLogin(BaseHandler):
    def get(self):
        global qq_msg
        if qq_msg.find('登陆成功') != -1:
            self.render('qqlogin.html', qqimgsrc='', weixinimgsrc='', qq_msg='已是登陆状态', weixin_msg='')
        else:
            qq_msg = ''
            ls_f = getLogin()
            self.render('qqlogin.html', qqimgsrc=ls_f, weixinimgsrc='', qq_msg='', weixin_msg='')

class web_QQLogin2(BaseHandler):
    def get(self):
        global qq_msg
        main()
        self.render('qqlogin.html', qqimgsrc=ls_f, weixinimgsrc='', qq_msg=qq_msg, weixin_msg='')

class insertES(threading.Thread):  # 入ES
    def run(self):
        global es_queue
        while True:
            if es_queue.qsize() > 0:

                maps = es_queue.get()
                try:
                    es = ESUtil()
                    # 执行updateByMobile。若存在会覆盖，若不存在会新增。
                    es.updateByMobile(maps['msg_id'], maps)
                    time.sleep(1)
                except Exception, e:
                    logger.info('%s执行入ES错误！！error：%s' % (maps['msg_id'], e.message))
                    es_queue.put(maps)
                logger.info('es_queue_size:' + str(es_queue.qsize()))
                print 'es_queue_size:' + str(es_queue.qsize())


class sendHttp(threading.Thread):  # 推送Http数据
    def run(self):
        global http_queue
        while True:
            if http_queue.qsize() > 0:

                try:
                    # for i in range(http_queue.qsize()):
                    qqmsgs = []
                    msg = http_queue.get()
                    qqmsgs.append(msg)

                    body = {}
                    body['qq'] = qqmsgs
                    http = HttpRequest()
                    headerDict = {
                        'Content-type': 'application/json'
                    }
                    jbody = json.dumps(body)
                    # res = http.setUrl('http://kg-streaming-api.kg.test/qq/callback/crawler').setHeader(
                    #     headerDict).setBody(jbody).post()

                    res = http.setUrl('http://api.puhuifinance.com/kg-streaming-api/qq/callback/crawler').setHeader(
                        headerDict).setBody(jbody).post()

                    # resp = json.loads(res)
                    if str(res).find('200') == -1:
                        # 接收失败，待重新消费
                        logger.info('send qqmsgs error. result= %s；qqmsgs size = %s' % (res, len(qqmsgs)))
                        for i in qqmsgs:
                            http_queue.put(i)
                    else:
                        logger.info('send qqmsgs success. result= %s；qqmsgs size = %s' % (res, len(qqmsgs)))

                except Exception, e:
                    logger.info('推送Http数据错误！！error：%s' % (e.message))
                    if qqmsgs:
                        for i in qqmsgs:
                            http_queue.put(i)
                logger.info('http_queue_size:' + str(http_queue.qsize()))
                # time.sleep(10)


def getPtqrToken(cookie):
    print cookie
    parser = execjs.compile("""
        function hash33(t) {
            for (var e = 0, i = 0, n = t.length; n > i; ++i){
                e += (e << 5) + t.charCodeAt(i);
            }
            return 2147483647 & e;
        }
    """)
    return parser.call("hash33", cookie)


def hash2(uin, ptvfwebqq):
    parser = execjs.compile("""

        function hash2(uin, ptvfwebqq){
            uin += "";
            var
            ptb = [];
            for (var i=0;i < ptvfwebqq.length;i++){
                var ptbIndex = i % 4;
                ptb[ptbIndex] ^= ptvfwebqq.charCodeAt(i);
            }
            var salt =["EC", "OK"];
            var uinByte =[];
            uinByte[0] = (((uin >> 24) & 0xFF) ^ salt[0].charCodeAt(0));
            uinByte[1] = (((uin >> 16) & 0xFF) ^ salt[0].charCodeAt(1));
            uinByte[2] = (((uin >> 8) & 0xFF) ^ salt[1].charCodeAt(0));
            uinByte[3] = ((uin & 0xFF) ^ salt[1].charCodeAt(1));
            var result =[];
            for (var i=0;i < 8;i++){
            if (i % 2 == 0)
                result[i] = ptb[i >> 1];
            else
                result[i] = uinByte[i >> 1];
            }
            return byte2hex(result);

        };
        function byte2hex(bytes){
            var hex = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'];
            var buf = "";

            for (var i=0;i<bytes.length;i++){
                buf += (hex[(bytes[i]>>4) & 0xF]);
                buf += (hex[bytes[i] & 0xF]);
            }
            return buf;
        }
        """)
    return parser.call("hash2", uin, ptvfwebqq)


def waitForLogin(ptloginsig, ptqrtoken):
    url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?ptqrtoken=%s&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-%s&js_ver=10227&js_type=1&login_sig=%s&pt_uistyle=40&aid=501004106&daid=164&mibao_css=m_webqq&' % (
        ptqrtoken, int(time.time()), ptloginsig)
    params = {
        'u1': 'http://w.qq.com/proxy.html'
    }
    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'accept': '*/*',
        'referer': 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?daid=164&target=self&style=40&mibao_css=m_webqq&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001'
    }

    r = myRequests.get(url=url, params=params, headers=headers, verify=False)
    r.encoding = 'utf-8'
    data = r.text
    print '--ptqrlogin------------------%s' % r.status_code
    # Cookie = r.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value
    print data
    retcode = ''
    if data.find('ptuiCB(\'0\'') != -1:
        # 登陆成功
        print '扫码登陆成功'
        # print r.cookies
        retcode = '扫码成功'
        # ptuiCB('0','0','http://ptlogin2.web2.qq.com/check_sig?pttype=1&uin=372643864&service=ptqrlogin&nodirect=0&ptsigx=4eb4498a7b45894fda09ebcc0049866ccb11083e0e41f8ae4ce87c6ca0cc32c2663da96d3c9555df7eafee345b8a3ebeb37909d8cd6f109a760152c6e15b0daf&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=&ptlang=2052&ptredirect=100&aid=501004106&daid=164&j_later=0&low_login_hour=0&regmaster=0&pt_login_type=3&pt_aid=0&pt_aaid=16&pt_light=0&pt_3rd_aid=0','0','登录成功！', 'AAAA');
        # 执行result中的check_sig链接
        headers = {
            'Accept-encoding': 'gzip, deflate',
            'Accept-language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Host': 'ptlogin2.web2.qq.com',
            'Connection': 'keep-alive'
        }
        # c = myRequests.cookies
        # c.set('p_skey', 'mOPxGjpJPku0tOwNIB0iJPhg5VpLydNy5iAg06bZyrc_', path='N/A', domain='N/A')
        # c.set('pt4_token', 'd4gV-u0ZQrUazEd6sLHK0vUDdUfsYToe66ACapivy9o_', path='N/A', domain='N/A')
        #
        # myRequests.cookies.update(c)

        i = data.find(',\'http://')
        j = data.find('\',\'0\',\'登录')
        url = data[i:j].replace(',\'http', 'http').replace('\',\'0\',\'登录', '').replace(
            '&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html', '')
        print url
        params = {'s_url': 'http://w.qq.com/proxy.html'}
        r = myRequests.get(url=url, params=params, headers=headers, allow_redirects=False)
        r.encoding = 'utf-8'

        print '--check_sig------------------%s' % r.status_code
        # Cookie = r.cookies
        # for item in Cookie:
        #     print 'Name = ' + item.name
        #     print 'Value = ' + item.value
    elif data.find('ptuiCB(\'66\'') != -1:
        retcode = '等待扫码'
    else:
        retcode = '登陆失败'
    time.sleep(3)
    print retcode
    return retcode


def waitForPoll2():
    global qq_msg, error_num
    try:
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Connection': 'keep-alive',
            'Content-Length': "148",
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'd1.web2.qq.com',
            'Origin': 'http://d1.web2.qq.com',
            'Referer': 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        url = 'http://d1.web2.qq.com/channel/poll2'
        params = {"ptwebqq": "" + ptwebqq + "", "clientid": 53999199, "psessionid": "" + psessionid + "", "key": ""}
        data = "r=%s" % json.dumps(params)
        logger.info('waitForPoll2 start--theOnlineTime is :%s' % theOnlineTime)
        r = myRequests.post(url=url, data=data, headers=headers, timeout=600)
        r.encoding = 'utf-8'
        data = r.json()
        print data
        print '16--poll2----------------------%s' % r.status_code
        logger.info('waitForPoll2 status_code:%s;---the data:%s' % (r.status_code, data))

        # copy cookie
        if r.cookies.get_dict():  # 保持cookie有效
            myRequests.cookies.update(r.cookies)

        if 'retcode' in data and data['retcode'] == 0:
            if "result" in data:
                print '16--msg------------%s' % json.dumps(data['result'][0], encoding='utf-8', ensure_ascii=False)
                logger.info(
                    'waitForPoll2 result:%s' % json.dumps(data['result'][0], encoding='utf-8', ensure_ascii=False))
                # 组装数据，保存本地ES
                sendMsg2Save(data['result'][0])
            time.sleep(1)
            return '200'
        elif 'retcode' in data and data['retcode'] == 103:
            if "result" in data:
                print '16--msg------------%s' % json.dumps(data['result'][0], encoding='utf-8', ensure_ascii=False)
                logger.info(
                    'waitForPoll2 result:%s' % json.dumps(data['result'][0], encoding='utf-8', ensure_ascii=False))
                # 组装数据，保存本地ES
                sendMsg2Save(data['result'][0])
            # 获取在线状态
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                'Connection': 'keep-alive',
                'Content-Type': 'utf-8',
                'Host': 'd1.web2.qq.com',
                'Referer': 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
            }
            url = 'http://d1.web2.qq.com/channel/get_online_buddies2?vfwebqq=%s&clientid=53999199&psessionid=%s&t=%s' % (
                vfwebqq, psessionid, int(time.time()))
            params = {}
            r = myRequests.get(url=url, data=params, headers=headers)
            r.encoding = 'utf-8'
            data = r.text
            logger.info('get_online_buddies2---status_code:%s;the data:%s' % (r.status_code, data))

            time.sleep(1)
            return '200'
        elif 'retcode' in data and data['retcode'] == 100001:
            qq_msg = 'QQ掉线'
            logger.error("主人..主人..您的QQ又掉线啦。。")
            return 'loginout'
        else:
            logger.info('waitForPoll2 ---loginout--- status_code:%s;the data:%s' % (r.status_code, data))
            if data['retcode'] == 100000:
                error_num = error_num + 1
            else:
                error_num = 0
            # 获取在线状态
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                'Connection': 'keep-alive',
                'Content-Type': 'utf-8',
                'Host': 'd1.web2.qq.com',
                'Referer': 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
            }
            url = 'http://d1.web2.qq.com/channel/get_online_buddies2?vfwebqq=%s&clientid=53999199&psessionid=%s&t=%s' % (
                vfwebqq, psessionid, int(time.time()))
            params = {}
            r = myRequests.get(url=url, data=params, headers=headers)
            r.encoding = 'utf-8'
            data = r.text
            logger.info('get_online_buddies2---status_code:%s;the data:%s' % (r.status_code, data))
            if str(r.status_code).find('200') != -1 and error_num < 100:
                return '200'
            else:
                qq_msg = 'QQ掉线'
                logger.error("主人..主人..您的QQ又掉线啦。。")
                return 'loginout'

    except Exception, e:
        logger.error('waitForPoll2 执行错误！！error：%s' % e.message)
        qq_msg = 'QQ掉线'
        logger.error("主人..主人..您的QQ又掉线啦。。")
        return 'loginout'


def sendMsg2Save(msg):
    try:
        """
        {
            'msg_id':'聊天记录流水号',
            'group_qq':'群号',
            'group_uin':'群uin',
            'group_name':'群名称',
            'group_member':'群成员',
            'time':'消息发送时间',
            'send_name':'发送人昵称',
            'send_qq':'发送QQ号',
            'send_uin':'发送uin',
            'msg':'消息'
        }
        """
        data = {}
        from_uin = msg['value']['from_uin']
        poll_type = msg['poll_type']
        data['msg_id'] = '%s%s' % (from_uin, msg['value']['msg_id'])
        data['group_qq'] = ''
        if poll_type.find('group_message') != -1:
            data['group_uin'] = msg['value']['group_code']
            # 获取对应的group_name
            global groupNames
            if data['group_uin'] in groupNames:
                data['group_name'] = groupNames[data['group_uin']]
            else:
                data['group_name'] = ''
                # print '-----------------group_code=%s,group_name=%s,groupNames=%s' % (
                # data['group_uin'], data['group_name'], groupNames)
        else:
            data['group_uin'] = ''
            data['group_name'] = ''
        data['group_member'] = ''
        data['time'] = msg['value']['time']
        data['send_name'] = ''
        data['send_qq'] = ''
        if poll_type.find('group_message') != -1:
            data['send_uin'] = msg['value']['send_uin']
        else:
            data['send_uin'] = from_uin

        # print len(msg['value']['content'])
        qqmsg = ''
        for i in range(len(msg['value']['content']) - 1):
            qqmsg = '%s%s' % (qqmsg, msg['value']['content'][i + 1])
        data['msg'] = qqmsg
        if len(qqmsg) < 1:
            return
        print 'qq msg -------------%s' % data
        global es_queue
        es_queue.put(data)
        logger.info('sendMsg2Save success data =%s' % json.dumps(data, encoding='utf-8', ensure_ascii=False))
    except Exception, e:
        logger.error('%s执行错误！！error：%s' % (msg, e.message))


def getMobiles(qqmsg):
    # 获取页面里所有的手机号或固话
    regex1 = r"1\d{10}|(1\d{2}-\d{4}-\d{4})|(1\d{2} \d{4} \d{4})"  # 手机号
    regex2 = r"0\d{11}|0\d{9}|[2-9]\d{7}|[2-9]\d{6}|[2-9]\d{5}|(\d{3,4}-\d{7,8})|(\d{3,4} \d{7,8})"  # 固话
    reobj = re.compile(regex1)
    reobj2 = re.compile(regex2)
    mobiles = []
    for match in reobj.finditer(qqmsg):
        mobile = match.group()
        mobile = str(mobile).strip().replace("-", "").replace(" ", "")
        if mobile and mobile.strip() and mobile.strip() not in str(mobiles):
            mobiles.append(mobile)
    for match in reobj2.finditer(qqmsg):
        mobile = match.group()
        mobile = str(mobile).strip().replace("-", "").replace(" ", "")
        if mobile and mobile.strip() and mobile.strip() not in str(mobiles):
            mobiles.append(mobile)
    return str(mobiles).replace('[', '').replace(']', '').replace(' ', '').replace('\'', '')


def getQQs(qqmsg):
    # 获取页面里所有QQ号
    regex = r"\d{11}|\d{10}|\d{9}|\d{8}|\d{7}|\d{6}"
    qqs = []
    if qqmsg.find('q') != -1 or qqmsg.find('Q') != -1:
        reobj = re.compile(regex)
        for match in reobj.finditer(qqmsg):
            qq = match.group()
            if qq and qq.strip() and qq.strip() not in str(qqs):
                qqs.append(qq)
    return str(qqs).replace('[', '').replace(']', '').replace(' ', '').replace('\'', '')


def getweixins(qqmsg):
    # 获取页面里所有QQ号
    regex = r"([v,V][0-9]*)|([v,V]:[0-9]*)|([v,V]：[0-9]*)"
    weixins = []
    reobj = re.compile(regex)
    for match in reobj.finditer(qqmsg):
        weixin = match.group()
        if weixin and weixin.strip() and weixin.strip() not in str(weixins):
            weixins.append(weixin)
    return str(weixins).replace('[', '').replace(']', '').replace(' ', '').replace('\'', '')


def getLogin():
    # 获取登陆二维码
    url = 'http://w.qq.com'

    global myRequests, uin, ptwebqq, psessionid, ptloginsig, ls_f
    ptloginsig = ''

    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }
    myRequests = requests.Session()
    myRequests.headers.update(headers)

    c = myRequests.cookies
    c.set('RK', 'SOM/B1jfSr', path='N/A', domain='N/A')
    c.set('pgv_pvi', '9556261888', path='N/A', domain='N/A')
    c.set('pgv_si', 's9674870784', path='N/A', domain='N/A')
    # c.set('ptui_loginuin', '372643864', path='N/A', domain='N/A')
    c.set('pgv_pvid', '607016366', path='N/A', domain='N/A')
    c.set('ptisp', 'cnc', path='N/A', domain='N/A')
    # c.set('ptcz', '64970365949dc5980fb8f85c59402f853adb52d805cb8c3035acef45d98e084f', path='N/A', domain='N/A')
    # c.set('pt_recent_uins','d9a2e3c9ae4d92671a96db432f31964967b215c82ac60546f0fabdbaecdf67321ca58c82dc5dc387815a0e4605f80ce0827ee8b1ae8e378c',path='N/A', domain='N/A')
    # c.set('pt2gguin', 'o0372643864', path='N/A', domain='N/A')
    myRequests.cookies.update(c)

    params = {}
    r = myRequests.get(url=url, params=params)
    r.encoding = 'utf-8'
    data = r.text
    # print data
    url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?daid=164&target=self&style=40&mibao_css=m_webqq&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001'
    r = myRequests.get(url=url, params=params, verify=False)
    r.encoding = 'utf-8'
    data = r.text
    Cookie = r.cookies
    for item in Cookie:
        # print 'Name = ' + item.name
        # print 'Value = ' + item.value
        if str(item.name).find('pt_login_sig') != -1:
            ptloginsig = item.value
    logger.info('-3--xlogin------------------------%s' % r.status_code)
    url = 'https://ssl.ptlogin2.qq.com/ptqrshow?appid=501004106&e=2&l=M&s=3&d=72&v=4&t=%s&daid=164' % int(time.time())
    r = myRequests.get(url=url, verify=False, params=params)

    Cookie = r.cookies
    for item in Cookie:
        # print 'Name = ' + item.name
        # print 'Value = ' + item.value
        if str(item.name).find('pt_login_sig') != -1:
            ptloginsig = item.value

    logger.info('请使用QQ扫描二维码以登录')

    logger.info('1--ptqrshow------------------------%s' % r.status_code)

    # main()
    # 返回二维码图片
    ls_f = base64.b64encode(r.content)  # 读取文件内容，转换为base64编码
    # f.close()
    print ls_f
    return ls_f

def main():
    global myRequests, uin, ptwebqq, vfwebqq, psessionid, ptloginsig, theOnlineTime, qq_msg
    theOnlineTime = time.time()

    # print '5--ptui_ver.js----------------------%s' % r.status_code
    url = 'https://ui.ptlogin2.qq.com/cgi-bin/report?id=358342&t=%s' % random.random
    params = {}
    headers = {
        'Host': 'ui.ptlogin2.qq.com',
        'Referer': 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?daid=164&target=self&style=40&mibao_css=m_webqq&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    r = myRequests.get(url=url, params=params, headers=headers, verify=False)
    r.encoding = 'utf-8'
    data = r.text
    Cookie = myRequests.cookies
    for item in Cookie:
        # print 'Name = ' + item.name
        # print 'Value = ' + item.value
        if str(item.name).find('pt_login_sig') != -1:
            ptloginsig = item.value
        if str(item.name).find('qrsig') != -1:
            qrsig = item.value
    ptqrtoken = getPtqrToken(qrsig)
    print '6--report----------------------%s' % r.status_code
    time.sleep(5)

    loginmsg = waitForLogin(ptloginsig, ptqrtoken)
    if loginmsg.find('扫码成功') == -1:
        qq_msg = loginmsg
        return loginmsg

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Host': 'w.qq.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    proxyurl = 'http://w.qq.com/proxy.html'
    params = {}
    r = myRequests.get(url=proxyurl, data=json.dumps(params), headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    # print data
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    print '7--proxy------------------------%s' % r.status_code
    headers = {
        'Referer': 'http://w.qq.com/proxy.html',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    proxyurl = 'http://web2.qq.com/web2_cookie_proxy.html'
    params = {}
    r = myRequests.get(url=proxyurl, data=json.dumps(params), headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    # print data
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    print '7--web2_cookie_proxy------------------------%s' % r.status_code

    # print '8--report----------------------%s' % r.status_code
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Host': 's.web2.qq.com',
        'Referer': 'http://w.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    proxyurl = 'http://s.web2.qq.com/proxy.html?v=20130916001&callback=1&id=1'
    params = {}
    r = myRequests.get(url=proxyurl, data=json.dumps(params), headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    # print data
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    print '9--proxy----------------------%s' % r.status_code
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Host': 's.web2.qq.com',
        'Referer': proxyurl,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://s.web2.qq.com/api/getvfwebqq?ptwebqq=&clientid=53999199&psessionid=&t=%s' % int(time.time())
    params = {}
    r = myRequests.get(url=url, data=json.dumps(params), headers=headers)
    r.encoding = 'utf-8'
    data = r.json()

    print data
    if 'retcode' in data and data['retcode'] == 0:
        vfwebqq = data['result']['vfwebqq']
    print '10--getvfwebqq----------------%s' % vfwebqq
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    headers = {
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Host': 'wspeed.qq.com',
        'Referer': 'http://w.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'https://wspeed.qq.com/w.cgi?appid=1000164&touin=null&releaseversion=SMARTQQ&frequency=1&commandid=%2F%2Fs.web2.qq.com%2Fapi%2Fgetvfwebqq&resultcode=0&tmcost=276'
    params = {}
    r = myRequests.get(url=url, data=json.dumps(params), headers=headers, verify=False)
    r.encoding = 'utf-8'
    data = r.text
    print '--w.cgi-----------%s' % r.status_code
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Host': 'd1.web2.qq.com',
        'Referer': 'http://w.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2'
    params = {}
    r = myRequests.get(url=url, data=json.dumps(params), headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    # print data
    print '11--proxy.html-------------------%s' % r.status_code
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    # 检查登陆结果
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-Length': "116",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'd1.web2.qq.com',
        'Origin': 'http://d1.web2.qq.com',
        'Referer': 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://d1.web2.qq.com/channel/login2'
    params = {"ptwebqq": "", "clientid": 53999199, "psessionid": "", "status": "online"}
    data = "r=%s" % json.dumps(params)
    r = myRequests.post(url=url, data=data, headers=headers)
    r.encoding = 'utf-8'
    data = r.json()
    # vfwebqq = ''
    print data
    if 'retcode' in data and data['retcode'] == 0:
        if 'uin' in data['result']:
            uin = data['result']['uin']
        if 'ptwebqq' in data['result']:
            ptwebqq = data['result']['ptwebqq']
        if 'psessionid' in data['result']:
            psessionid = data['result']['psessionid']

    # Cookie = myRequests.cookies
    logger.info('12--login2---------------------%s' % r.status_code)
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    # 获取好友
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-Length': "148",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 's.web2.qq.com',
        'Origin': 'http://s.web2.qq.com',
        'Referer': 'http://s.web2.qq.com/proxy.html?v=20130916001&callback=1&id=1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://s.web2.qq.com/api/get_user_friends2'
    hash = hash2(uin, ptwebqq)
    params = {"vfwebqq": "" + vfwebqq + "", "hash": "" + hash + ""}
    data = "r=%s" % json.dumps(params)
    r = myRequests.post(url=url, data=data, headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    logger.info('get_user_friends------:%s' % data)
    global myuin
    dataj = json.loads(data)
    if 'info' in dataj['result']:
        friends = dataj['result']['info']
        for gname in friends:
            if 'nick' in gname and str(gname['nick']).find('Leon') != -1:
                myuin = gname['uin']

    # 获取群组
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-Length': "148",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 's.web2.qq.com',
        'Origin': 'http://s.web2.qq.com',
        'Referer': 'http://s.web2.qq.com/proxy.html?v=20130916001&callback=1&id=1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://s.web2.qq.com/api/get_group_name_list_mask2'
    hash = hash2(uin, ptwebqq)
    params = {"vfwebqq": "" + vfwebqq + "", "hash": "" + hash + ""}
    data = "r=%s" % json.dumps(params)
    r = myRequests.post(url=url, data=data, headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    logger.info('get_group_name_list_mask------:%s' % data)
    print '14--get_group_name_list_mask2----------------------%s' % r.status_code
    # 解析群组
    global groupNames
    dataj = json.loads(data)
    if 'gnamelist' in dataj['result']:
        gnamelist = dataj['result']['gnamelist']
        for gname in gnamelist:
            groupNames[gname['gid']] = gname['name']
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value
    # guin = ''
    # 获取群组QQ
    # url = 'http://s.web2.qq.com/api/get_friend_uin2?tuin='+guin+'&type=1&vfwebqq='+vfwebqq+'&t='+int(time.time())
    # r = myRequests.post(url=url, data=data, headers=headers)
    # r.encoding = 'utf-8'
    # data = r.text
    # logger.info('get_group_name_QQ------:%s' % data)

    # 获取在线状态
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-Type': 'utf-8',
        'Host': 'd1.web2.qq.com',
        'Referer': 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    url = 'http://d1.web2.qq.com/channel/get_online_buddies2?vfwebqq=%s&clientid=53999199&psessionid=%s&t=%s' % (
        vfwebqq, psessionid, int(time.time()))
    params = {}
    r = myRequests.get(url=url, data=params, headers=headers)
    r.encoding = 'utf-8'
    data = r.text
    logger.info('get_online_buddies--:%s' % data)
    print '15--get_online_buddies2----------------------%s' % r.status_code
    # Cookie = myRequests.cookies
    # for item in Cookie:
    #     print 'Name = ' + item.name
    #     print 'Value = ' + item.value

    logger.info("您的QQ登陆成功。。")
    qq_msg = '登陆成功。'
    # 循环获取即时聊天记录
    p = dowloader()
    p.start()
    return True

class dowloader(threading.Thread):  # 下载线程
    def run(self):
        while waitForPoll2() == '200':
            pass

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "../tornadoTemp"),
    'static_path': os.path.join(os.path.dirname(__file__), "../static"),
    'static_url_prefix': '/static/',
}

application = tornado.web.Application([
    (r"/qqlogin", web_QQLogin),
    (r"/qqlogin2", web_QQLogin2)
], **settings)

if __name__ == "__main__":

    # 请求地址：http://localhost:7778/qqlogin
    port = 7778
    application.listen(port)
    logger.info('程序启动！！监听端口为：%s' % port)
    tornado.ioloop.IOLoop.instance().start()