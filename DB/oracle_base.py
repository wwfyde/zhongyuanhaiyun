# !/usr/bin/env python
# -*- coding=utf-8 -*-

import time
import os
import traceback
import logging
# 兼容中文
# os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import cx_Oracle as db


class OracleBase(object):
    """
    base class
    """
    name = 'oracleBase'

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.username = None  
        self.passwd = None
        self.host = None
        self.port = None
        self.sid = None
        
    def init(self, dbConfig):
        logging.info("start to connect to db, config:" + str(dbConfig))
        self.username = dbConfig["username"]
        self.passwd = dbConfig["password"]
        #self.host = dbConfig["host"]
        #self.port = dbConfig["port"]
        #self.sid = dbConfig["sid"]
        
        self.TNSNAME = dbConfig["tnsname"]
        
        self.connection()

# ############################## connection ##################################

    def connection(self):
        """
        连接数据库
        """
        try:
            #dsn = db.makedsn(self.host, self.port, self.sid)  
            #self.conn = db.connect(self.username, self.passwd, dsn)  
            self.conn = db.connect(self.username + '/' + self.passwd + self.TNSNAME)
            logging.info("connected")
        except:
            logging.exception("connect error")

    def get_cursor(self):
        while (not self.conn):
            logging.warning("try get Connection ..............")
            time.sleep(5)
            self.connection()

        self.cursor = self.conn.cursor()
        return self.cursor

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

# ############################## sql ##################################

    def select_sql(self, sql):
        """
    oracle 查询
    return [{},{}]
        """
        cursor = self.get_cursor()
        logging.info("execute sql:" + sql)
        try:
            cursor.execute(sql)
        except:
            logging.exception("error when execute sql")
            logging.exception(traceback.format_exc())
        # rows = cursor.fetchall()
        ret = self.rows_to_dict(cursor)
        if self.cursor:
            self.cursor.close()
        return ret
    
    def rows_to_dict(self, cursor):
        columns = [i[0] for i in cursor.description]
        logging.info("change oracle rows to dict, columns:" + str(columns))
        ret = [dict(zip(columns, row)) for row in cursor]
        logging.info("dict:" + str(ret))
        return ret
    
    def update_sql(self, sql):
        """
     update_sql
        """
        try:
            logging.info("sql:" + sql)
            cursor = self.get_cursor()
            cursor.execute(sql)
            self.conn.commit()
        except BaseException as e:
            logging.exception(traceback.format_exc())
            cursor = None
            self.connection()
