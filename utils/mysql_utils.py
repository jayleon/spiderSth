#!/usr/bin/python
# coding:utf-8
# mysql工具类

import pymysql
import os, json, time
from DBUtils.PooledDB import PooledDB
import sys
import db_config as Config


class MysqlUtil(object):
    # 连接池对象
    __pool = None

    def __init__(self, host=Config.DB_TEST_HOST, port=Config.DB_TEST_PORT, user=Config.DB_TEST_USER,
                 password=Config.DB_TEST_PASSWORD, db=Config.DB_TEST_DBNAME):
        # 数据库构造函数，从连接池中取出连接，并生成操作游标
        try:
            self.conn = MysqlUtil.__getConn(host, port, user, password, db)
            self.cursor = self.conn.cursor()
        except Exception, e:
            error = 'Connect failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            print error
            sys.exit()

    @staticmethod
    def __getConn(host, port, user, password, db):
        """
        @summary: 静态方法，从连接池中取出连接
        @return mysql.connection
        """
        if MysqlUtil.__pool is None:
            print "初始化连接池！！"
            __pool = PooledDB(creator=pymysql, mincached=Config.DB_MIN_CACHED, maxcached=Config.DB_MAX_CACHED,
                              maxshared=Config.DB_MAX_SHARED, maxconnections=Config.DB_MAX_CONNECTIONS,
                              blocking=Config.DB_BLOCKING, maxusage=Config.DB_MAX_USAGE,
                              setsession=Config.DB_SET_SESSION,
                              host=host, port=port,
                              user=user, passwd=password,
                              db=db, use_unicode=False, charset=Config.DB_CHARSET)
        return __pool.connection()

    # 针对读操作返回结果集
    def _exeCute(self, sql=''):
        try:
            self.cursor.execute(sql)
            records = self.cursor.fetchall()
            return records
        except pymysql.Error, e:
            error = 'MySQL execute failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            print error

    # 插入单条数据
    def insertOne(self, sql, value=None):
        """
        @summary: 向数据表插入一条记录
        @param sql:要插入的ＳＱＬ格式
        @param value:要插入的记录数据tuple/list
        @return: insertId 受影响的行数
        """
        self._exeCuteCommit(sql, value)
        return self.__getInsertId()

    def __getInsertId(self):
        """
        获取当前连接最后一次插入操作生成的id,如果没有则为０
        """
        self.cursor.execute("SELECT @@IDENTITY AS id")
        result = self.cursor.fetchall()
        return result[0]['id']

    def __query(self, sql, param=None):
        if param is None:
            count = self.cursor.execute(sql)
        else:
            count = self.cursor.execute(sql, param)
        return count

    def insertMany(self, sql, values=None):
        """
        @summary: 向数据表插入多条记录
        @param sql:要插入的ＳＱＬ格式
        @param values:要插入的记录数据tuple(tuple)/list[list]
        @return: count 受影响的行数
        """
        try:
            if values is None:
                count = self.cursor.executemany(sql)
            else:
                count = self.cursor.execute(sql, values)
            self.conn.commit()
        except pymysql.Error, e:
            self.conn.rollback()
            error = 'MySQL execute failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            print error
            sys.exit()
        return count

    def begin(self):
        """
        @summary: 开启事务
        """
        self.conn.autocommit(0)

    def end(self, option='commit'):
        """
        @summary: 结束事务
        """
        if option == 'commit':
            self.conn.commit()
        else:
            self.conn.rollback()

    # 针对更新,删除,事务等操作失败时回滚
    def _exeCuteCommit(self, sql='', arg=None):
        try:
            if arg is None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, arg)
            self.conn.commit()
        except pymysql.Error, e:
            self.conn.rollback()
            error = 'MySQL execute failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            print error
            # sys.exit()

    def close(self):
        if self.conn:
            print "关闭连接！！"
            self.conn.close()
            self.cursor.close()


def write_log(line):
    tm = time.localtime(time.time())
    now = time.strftime("%Y%m%d%H%M%S", tm)
    today = time.strftime("%Y%m%d", tm)
    log_file = os.path.join('log', ('getsql_log.%s' % today))
    try:
        of = open(log_file, 'a+')
        of.write("%s -- %s\n" % (now, line))
        of.flush()
        of.close()
    except:
        print ("open %s failed" % log_file)


def write_sql(sqlStr):
    if sqlStr != "":
        time_interval = 60 * 2
        now_ts = int(time.time()) / time_interval * time_interval
        now_tm = time.localtime(now_ts)
        now = time.strftime("%Y%m%d%H%M%S", now_tm)

        filename = "%s/vertical_%s.sql" % ("./sql_data", now)
        if os.path.exists(filename) == False:
            file_obj = open(filename, 'a+')
            file_obj.write("SET NAMES utf8;\n")
            file_obj.write(sqlStr + "\n")
        else:
            file_obj = open(filename, 'a+')
            file_obj.write(sqlStr + "\n")
        file_obj.close()


def Dict2Sql(result_map, table_name, columns, int_columns=[]):
    if type(table_name) != str or table_name.strip == '':
        print "Dict2Sql Error: invalid table_name[%s]" % table_name
    temp_map = {}
    for key_str in columns:
        if key_str in result_map:
            value = result_map[key_str]
        if type(value) == str:
            temp_map[key_str] = value.strip()
        elif type(value) == unicode:
            temp_map[key_str] = value.encode('utf8').strip()
        else:
            temp_map[key_str] = str(value).strip()
        if key_str in int_columns:
            temp_map[key_str] = int(temp_map[key_str])

    sql = "INSERT IGNORE INTO %s SET " % table_name
    for k, v in temp_map.items():
        kv = r"`%s`='%s'," % (k, pymysql.escape_string(v))
        sql += kv
    sql = sql[0:-1]
    sql += ";"
    write_sql(sql)
    return sql


def update_tbl(sql_list):
    try:
        conn = MysqlUtil()
        cur = conn.cursor
        cur.execute('set names utf8')
        for element in sql_list:
            print element
            cur.execute(element)
        conn.end()
        cur.close()
        conn.close()

    except pymysql.Error, e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        write_log("Mysql Error %d: %s" % (e.args[0], e.args[1]))


person_file = '../data/person_'
company_file = '../data/company_'
def get_result(page):  # 处理数据
    try:
        result_data = page[page.find('{"result":[') + 10:page.find(', "otherinfo":')]
        result_list = json.loads(result_data)
        for item in result_list:
            try:
                item['regDate'] = time.strftime("%Y年%m月%d日", time.strptime(item["regDate"], "%Y%m%d"))
                temp_str = json.dumps(item, ensure_ascii=False)
                if len(item["iname"]) > 9 and len(item["cardNum"]) < 15 and item['businessEntity']:
                    company_insert_tbl(item)
                    f = open(company_file + time.strftime('%Y%m%d'), 'a')
                    f.write(temp_str + '\n')
                    f.close()
                else:
                    person_insert_tbl(item)
                    f = open(person_file + time.strftime('%Y%m%d'), 'a')
                    f.write(temp_str + '\n')
                    f.close()
            except Exception as ex:
                try:
                    temp_str = json.dumps(item, ensure_ascii=False)
                    f = open('err_data.txt', 'a')
                    f.write(temp_str + '\n')
                    f.close()
                except:
                    time.sleep(1)
                print 'Find exception  --  %s' % ex
            return True
    except Exception as ex:
        print 'Find exception  --  %s' % ex
        time.sleep(1)


def dict_turn_sql(result_map, table_name, columns, int_columns=[]):
    """生成sql语句

    Args:
        result_map: 需要入库的数据
        table_name: 需要入的表
        columns: 表的全部字段名
    """
    if not isinstance(table_name, str) or table_name.strip == '':
        print "Dict2Sql Error: invalid table_name[%s]" % table_name

    temp_map = {}
    for key_str in columns:
        if key_str in result_map:
            value = result_map[key_str]
            if isinstance(value, str):
                temp_map[key_str] = value.strip()
            elif isinstance(value, unicode):
                temp_map[key_str] = value.encode('utf8').strip()
            else:
                temp_map[key_str] = str(value).strip()

            if key_str in int_columns:
                temp_map[key_str] = int(temp_map[key_str])
        else:
            # temp_map[key_str] = '本样本无此字段'
            temp_map[key_str] = ''

    sql = "INSERT IGNORE INTO %s SET " % table_name
    for key, value in temp_map.items():
        temp_str = r"`%s`='%s'," % (key, pymysql.escape_string(value))
        sql += temp_str
    sql = sql[0:-1]
    sql += ";"
    write_sql(sql)
    return sql


def person_insert_tbl(result_map):
    """失信人数据入库,将数据中的key转成表中的key

    Args:
        result_map: 要入库的数据
    """
    insert_map = {}
    columns = ['user_id', 'iname', 'caseCode', 'age', 'sexy', 'focusNumber',
               'cardNum', 'courtName', 'areaName', 'partyTypeName', 'gistId',
               'regDate', 'gistUnit', 'duty', 'performance', 'performedPart',
               'unperformPart', 'disruptTypeName', 'publishDate', 'inserttime',
               'updatetime']
    insert_map['iname'] = result_map['iname']
    insert_map['caseCode'] = result_map['caseCode']
    insert_map['age'] = result_map['age']
    insert_map['sexy'] = result_map['sexy']
    insert_map['cardNum'] = result_map['cardNum']
    insert_map['courtName'] = result_map['courtName']
    insert_map['areaName'] = result_map['areaName']
    insert_map['partyTypeName'] = result_map['partyTypeName']
    insert_map['gistId'] = result_map['gistId']
    insert_map['regDate'] = result_map['regDate']
    insert_map['gistUnit'] = result_map['gistUnit']
    insert_map['duty'] = result_map['duty']
    insert_map['performance'] = result_map['performance']
    insert_map['disruptTypeName'] = result_map['disruptTypeName']
    insert_map['publishDate'] = result_map['publishDate']
    cur_time = time.strftime('%Y-%m-%d %H:%M:%S')
    insert_map['inserttime'] = cur_time
    insert_map['updatetime'] = cur_time

    sql_list = []
    sql_str = dict_turn_sql(insert_map, 'sx_negative_person', columns)
    sql_list.append(sql_str)
    update_tbl(sql_list)


def company_insert_tbl(result_map):
    """失信人搜索结果数据入库,将数据中的key转成表中的key

    Args:
        result_map: 要入库的数据
    """
    insert_map = {}
    columns = ['company_name', 'reg_number', 'iname', 'card_num',
               'business_entity', 'reg_date', 'case_code', 'court_name',
               'area_name', 'gist_id', 'gist_unit', 'duty', 'performance',
               'disrupt_type_name', 'publish_date']
    insert_map['company_name'] = result_map['iname']
    insert_map['iname'] = result_map['iname']
    insert_map['card_num'] = result_map['cardNum']
    insert_map['business_entity'] = result_map['businessEntity']
    insert_map['reg_date'] = result_map['regDate']
    insert_map['case_code'] = result_map['caseCode']
    insert_map['court_name'] = result_map['courtName']
    insert_map['area_name'] = result_map['areaName']
    insert_map['gist_id'] = result_map['gistId']
    insert_map['gist_unit'] = result_map['gistUnit']
    insert_map['duty'] = result_map['duty']
    insert_map['performance'] = result_map['performance']
    insert_map['disrupt_type_name'] = result_map['disruptTypeName']
    insert_map['publish_date'] = result_map['publishDate']

    sql_list = []
    sql_str = dict_turn_sql(insert_map, 'crawler_credit_com_dishonest_info',
                            columns)
    sql_list.append(sql_str)
    update_tbl(sql_list)


if __name__ == "__main__":
    conn = MysqlUtil()
    conn._exeCuteCommit("UPDATE black_info_negative set is_es = '0' WHERE batch_id = '20160711144957999';")
