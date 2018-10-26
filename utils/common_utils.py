#!/usr/bin/python
# coding:utf-8
# 公共工具类

import codecs
import csv
import re, json


def compilePhone(phone):
    # 正则匹配电话号码
    if phone is not None and phone.strip():
        p2 = re.compile('1[34578]\\d{9}')
        phonematch = p2.match(phone)
        if phonematch:
            return True
    return False


def load_normal_list(path):
    normal_list = []
    file_object = open(path, 'rb')
    for line in file_object:
        # 解决出现\xef\xbb\xbf…的问题
        line = line.decode("utf-8-sig").encode("utf-8")
        line = line.replace('\r', '').replace('\n', '')
        # print line
        if line.strip():
            normal_list.append(line.strip())
    return normal_list

def load_normal_str(path):
    normal_mobile_list = ''
    file_object = open(path, 'rb')
    return file_object.read()


def load_category(path):
    category = {}
    file_object = open(path, 'rb')
    for line in file_object:
        line = line.replace('\r', '').replace('\n', '')
        print line
        key = line.split(" ")[0]
        vv = line.split(" ")[1]
        category[key] = vv
    return category


def compilePhone2(phone):
    # 正则匹配电话号码，包含：132****7926
    if phone is not None and phone.strip():
        p2 = re.compile('1[3458]\\d{9}|1[3458]\\d{1}\*\*\*\*\\d{4}')
        phonematch = p2.match(phone)
        if phonematch:
            return True
    return False


def compilePhone3(phone):
    # 正则匹配电话号码\固话
    if phone is not None and phone.strip():
        p2 = re.compile('^((0\d{2,3}-\d{7,8})|(1[3584]\d{9}))')
        phonematch = p2.match(phone)
        if phonematch:
            return True
    return False


def isNum(something):
    if something is not None and something.strip():
        p2 = re.compile('^(-|\+)?\d+$')
        phonematch = p2.match(something)
        if phonematch:
            return True
    return False


def compileIdNo(idno):
    # 正则匹配身份证
    if idno is not None and idno.strip():
        p2 = re.compile('^([1-9]\d{5}([123]\d{3}|\d{2})(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])(\d{3}[0-9xX]|\d{1}))$')
        idnomatch = p2.match(idno)
        if idnomatch:
            return True
    return False


def compileChinese(chi):
    # 正则匹配中文
    if chi is not None and chi.strip():
        chi = unicode(chi, 'utf8')
        p2 = re.compile(u"[\u4e00-\u9fa5]+")
        chimatch = p2.match(chi)
        if chimatch:
            return True
    return False


# MD5加密
def md5(str):
    import hashlib
    import types
    if type(str) is types.StringType:
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()
    else:
        return ''


# json转csv
def json2CSV(path, jsonname, csvname):
    # 保存抓取数据为csv文件
    csvName = '%s/%s' % (path, csvname)
    csvfile = file(csvName, 'ab')
    csvfile.write(codecs.BOM_UTF8)
    writer = csv.writer(csvfile)
    jsonname = '%s/%s' % (path, jsonname)
    file_object = open(jsonname, 'rb')
    for line in file_object:
        line = line.replace('\r', '').replace('\n', '')
        # print line
        if 'applist-index' in line:
            continue
        jo = json.loads(line)
        # print jo
        resultdata = []
        if jo:
            for key in jo.keys():
                value = ''
                if isinstance(jo[key], unicode):
                    value = jo[key].encode("UTF-8")
                    # print value
                else:
                    value = jo[key]
                resultdata.append(value)
            writer.writerow(resultdata)
            # break
    csvfile.close()

def get_dates_by_years(start, end):
    import datetime

    dates = []
    datestart = datetime.datetime.strptime(start, '%Y-%m-%d')
    dateend = datetime.datetime.strptime(end, '%Y-%m-%d')

    while datestart < dateend:
        datestart += datetime.timedelta(days=1)
        # print datestart.strftime('%Y-%m-%d')
        dates.append(datestart.strftime('%Y-%m-%d'))

    return dates

if __name__ == '__main__':
    # a = [[1, 2], [3, 4], [5, 6], [7, 8]]
    # print a[1][1]
    # print 'ok'
    # # load_normal_ips()
    # isok = isNum('112200s')
    # print isok
    # while True:
    # print random.randint(12, 20)
    # json2CSV('./','user.bulk.json','applist2.csv')
    print compilePhone3('186123198088991817');
    get_dates_by_years('','');
