#!/usr/bin/python
# coding:utf-8
# Elasticsearch工具类

import time, datetime, sys
from elasticsearch import Elasticsearch,helpers

import logging
from logging.handlers import TimedRotatingFileHandler

ES_HOST = '127.0.0.1'
ES_PORT = 9200
ES_INDEX = 'my-es-index'
ES_TYPE = 'my-es-type'

reload(sys)
sys.setdefaultencoding('utf-8')

log_file_path = '../log/es_utils.log'
logger = logging.getLogger('es_utils.py')
ch = logging.StreamHandler()
th = TimedRotatingFileHandler(log_file_path, when="MIDNIGHT", interval=1, backupCount=7)
formatter = logging.Formatter('%(name)s ：%(lineno)d ------ %(asctime)s------ %(levelname)s ------ %(message)s',
                              '%a, %d %b %Y %H:%M:%S', )
ch.setFormatter(formatter)
th.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(th)
logger.setLevel(logging.INFO)

class ESUtil:
    def __init__(self, host=None, port=None, index=None, type=None):
        if host is None:
            self.host = ES_HOST
        else:
            self.host = host
        if port is None:
            self.port = ES_PORT
        else:
            self.port = port
        if index is None:
            self.index = ES_INDEX
        else:
            self.index = index
        if type is None:
            self.type = ES_TYPE
        else:
            self.type = type
        self.ES = Elasticsearch([{'host': self.host, 'port': self.port}])

    # 筛选条件：指定手机号
    def searchByMobile(self, mobile):
        body = {
            "query": {
                "term": {
                    "_id": mobile
                }
            }
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定id
    def searchById(self, id):
        body = {
            "query": {
                "term": {
                    "_id": id
                }
            }
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定ids(数组)
    def searchByIds(self, ids):
        body = {
            "ids": ids
        }
        return self.ES.mget(body=body, index=self.index, doc_type=self.type)

    # 筛选条件：指定手机号、写入时间一月内的
    def searchByMobileOneMonthAgo(self, mobile):
        timestamp = month_get(datetime.datetime.now(), 30)
        body = {
            "query": {
                "filtered": {
                    "query": {"match": {"_id": mobile}},
                    "filter": {"range": {"timestamp": {'gt': timestamp}}}
                }
            }
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定手机号、写入时间n月内的
    def searchByMobileSomeMonthAgo(self, mobile, days):
        timestamp = month_get(datetime.datetime.now(), days)
        body = {
            "query": {
                "filtered": {
                    "query": {"match": {"_id": mobile}},
                    "filter": {"range": {"timestamp": {'gt': timestamp}}}
                }
            }
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定手机号、url有效的、长度200
    def searchByMobile4Sth(self, mobile):
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "mobile": mobile
                            }
                        },
                        {
                            "term": {
                                "mark": "0"
                            }
                        }
                    ],
                    "must_not": [],
                    "should": []
                }
            },
            "from": 0,
            "size": 200,
            "sort": [],
            "aggs": {}
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定snapshot、url有效的、长度200
    def searchBySnapshot4Sth(self, snapshot):
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "snapshot": snapshot
                            }
                        },
                        {
                            "term": {
                                "mark": "0"
                            }
                        }
                    ],
                    "must_not": [],
                    "should": []
                }
            },
            "from": 0,
            "size": 200,
            "sort": [],
            "aggs": {}
        }
        return self.ES.search(index=self.index, body=body)

    # 插入搜索结果
    def insert_search_results(self, obj):
        return self.ES.index(index=self.index, doc_type=self.type, body=obj)

    # 指定手机号，入ES
    def insertByMobile(self, mobile, maps):
        return self.ES.index(index=self.index, doc_type=self.type, id=mobile, body=maps)

    # 指定id，入ES
    def insertById(self, id, maps):
        return self.ES.index(index=self.index, doc_type=self.type, id=id, body=maps)

    # 根据指定手机号，更新maps里面的值
    def updateByMobile(self, mobile, maps):
        body = {"doc": maps, "doc_as_upsert": True}
        return self.ES.update(index=self.index, doc_type=self.type, id=mobile, body=body)

    # 根据指定id，更新maps里面的值
    def updateMarkByid(self, id, maps):
        body = {"doc": maps, "doc_as_upsert": True}
        return self.ES.update(index=self.index, doc_type=self.type, id=id, body=body)

    # 筛选条件：指定手机号、联系次数最多的前size个
    def searchByMobileLimitSize(self, mobile, size):
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "personalPhone": mobile
                            }
                        }
                    ],
                    "must_not": [],
                    "should": []
                }
            },
            "from": 0,
            "size": size,
            "sort": [{"contactTimes": "desc"}],
            "aggs": {}
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定查询字段名和值、写入时间最晚的前size个
    def searchByKeyLimitSize(self, key, value, size):
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                key: value
                            }
                        }
                    ],
                    "must_not": [],
                    "should": []
                }
            },
            "from": 0,
            "size": size,
            "sort": [{"request_time": "desc"}],
            "aggs": {}
        }
        return self.ES.search(index=self.index, body=body)

    # 筛选条件：指定多个查询字段名（数组）、写入时间最晚的前size个
    def searchByKeysLimitSize(self, keys, value, size):
        body = {
            "query": {
                "multi_match": {
                  "query": value,
                  "type": "most_fields",
                  "fields": keys
                }
              },
            "from": 0,
            "size": size,
            "sort": [{"request_time": "desc"}],
            "aggs": {}
        }

        return self.ES.search(index=self.index, body=body)

    def searchCount(self):
        body = {
            "aggs": {
                "uniq_streets": {
                    "cardinality": {
                        "field": "personalPhone"
                    }
                }
            }
        }
        return self.ES.search(index=self.index, body=body)

    def searchDSL(self, body):
        return self.ES.search(index=self.index, body=body)

    def deleteById(self, id):
        self.ES.delete(index=self.index,doc_type=self.type,id=id)

    def searchErrorDate(self,gt,lt,from_):
        body ={
            "fields": ["title"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gt": gt,
                                    "lt": lt
                                }
                            }
                        }
                    ],
                    "must_not": [],
                    "should": []
                }
            },
            "from": from_,
            "size": 2000
        }
        es_result = helpers.scan(
            client=self.ES,
            query=body,
            scroll='5m',
            index=self.index,
            doc_type=self.type,
            timeout='1m'
        )
        return es_result

    def searchByScroll_id(self,scroll_id):

        return self.ES.scroll(scroll_id)

# 获取指定日期一月前的日期，返回毫秒值
def month_get(d, days):
    dayscount = datetime.timedelta(days=days)
    dayto = d - dayscount
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 0, 0, 1)
    # print date_to
    t = date_to.timetuple()
    timeStamp = int(time.mktime(t))
    return timeStamp

# 获取指定日期一月前的日期，返回yyyy-MM-dd字符串
def time4StrSday(d, days):
    dayscount = datetime.timedelta(days=days)
    dayto = d - dayscount
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 0, 0, 1)
    # print date_to
    t = date_to.strftime('%Y-%m-%d')
    return t


# 获取指定日期N分钟前的日期，返回毫秒值
def month_get_min(d, min):
    dayscount = datetime.timedelta(minutes=min)
    dayto = d - dayscount
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 0, 0, 1)
    # print date_to
    t = dayto.timetuple()
    timeStamp = int(time.mktime(t))
    return timeStamp

# 获取指定日期N分钟前的日期，返回yyyy-MM-dd字符串
def time4StrSMin(d, min):
    dayscount = datetime.timedelta(minutes=min)
    dayto = d - dayscount
    date_to = datetime.datetime(dayto.year, dayto.month, dayto.day, 0, 0, 1)
    # print date_to
    t = dayto.strftime('%Y-%m-%d %H:%M')
    # print t
    return t

def get_result_list(es_result):
    final_result = []
    for item in es_result:
        final_result.append(item['_source'])
    return final_result

if __name__ == "__main__":
    es = ESUtil()
    data = {}
    data['msg_id'] = '1212121212121212'
    data['group_qq'] = '123'
    data['group_uin'] = '234'
    data['group_name'] = 'QQ群名1'
    data['group_member'] = 'QQ群成员1,QQ群成员2,QQ群成员3'
    data['time'] = '1504232728'
    data['send_name'] = '发言人QQ昵称'
    data['send_qq'] = '222'
    data['send_uin'] = '111'
    data['msg_mobiles'] = '13811223345,18611223345'
    data['msg_qqs'] = '111,222'
    data['msg_vs'] = '333,444'
    data['msg'] = '聊天内容'

    es = ESUtil()
    # 执行updateByMobile。若存在会覆盖，若不存在会新增。
    es.updateByMobile(data['msg_id'], data)
