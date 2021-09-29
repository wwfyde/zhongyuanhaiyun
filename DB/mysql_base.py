# !/usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import time
import traceback

import pymysql
import pymysql.cursors
import logging


class MysqlBase(object):
    """
    base class
    """
    name = 'mysqlBase'

    def __init__(self):
        self.host = None
        self.port = None
        self.user = None
        self.passwd = None
        self.db = None
        self.conn = None
        self.cursor = None
# ############################## connection ##################################
   
    def init(self,dbConfig):
        print("CustomDBBase:" + str(dbConfig))
        self.host = dbConfig['host']
        self.port = dbConfig['port']
        self.user = dbConfig['user']
        self.passwd = dbConfig['passwd']
        self.db = dbConfig['db']
        self.connection()
        
    def connection(self):
        """
        实现mysql的连接
        """
        try:
            self.conn = pymysql.connect(
                                host=self.host,
                                port=self.port,
                                user=self.user,
                                passwd=self.passwd,
                                db=self.db,
                                charset='utf8',
                                cursorclass=pymysql.cursors.DictCursor
                            )
        except BaseException as e:
            logging.exception("Error Get Connection From Mysql .......................")

    def get_cursor(self):
        while (not self.conn):
            logging.warn("try get Connection ..............")
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

    def select_sql(self, sql, args=None):
        """
    mysql 查询
        return [{},{}]
        """
        rows = []
        try:
            logging.info("execute sql:"+sql)
            cursor = self.get_cursor()
            cursor.execute("SET NAMES UTF8")
            cursor.execute(sql, args)
            rows = cursor.fetchall()
            rows = list(rows)
        except:
            logging.exception("error when execute sql")
            logging.exception(traceback.format_exc())
        return rows
    
    def update_sql(self, sql):
        """
        此处代码为示例，根据实际需要修改
        return [{},{}]
        """
        try:
            logging.info("sql:"+sql)
            cursor = self.get_cursor()
            cursor.execute("SET NAMES UTF8")
            cursor.execute(sql)
            self.conn.commit()
        except BaseException as e:
            logging.exception(traceback.format_exc())
            cursor = None;
            self.connection()