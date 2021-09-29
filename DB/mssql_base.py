# !/usr/bin/env python
# -*- coding=utf-8 -*-

import time
import traceback
import pymssql as db
import logging

class MSsqlBase(object):
    """
    base class
    """
    name = 'mssqlBase'

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.user = None  
        self.pwd = None
        self.host = None
        self.db = None
        
    def init(self,dbConfig):
        logging.info("start to connect to db, config:" + str(dbConfig))
        self.user = dbConfig["user"]
        self.pwd = dbConfig["pwd"]
        self.host = dbConfig["host"]
        self.db = dbConfig["db"]
        self.connection()

# ############################## connection ##################################

    def connection(self):
        """
        连接数据库
        """
        try:
            self.conn = db.connect(host=self.host,user=self.user,password=self.pwd,database=self.db,charset="utf8"
                                   ,as_dict = True)  
        except:
            logging.exception("connect error")
            
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

    def select_sql(self, sql):
        logging.info("start to select audio dim, sql:"+sql)
        """
    select_sql
        """
        rows = []
        try:
            cursor = self.get_cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
        except:
            logging.exception("error when execute sql")
            logging.exception(traceback.format_exc())
        return rows
    
    def update_sql(self, sql):
        """
     update_sql
        """
        try:
            logging.info("sql:"+sql)
            cursor = self.get_cursor()
            cursor.execute(sql)
            self.conn.commit()
        except BaseException as e:
            logging.exception(traceback.format_exc())
            cursor = None;
            self.connection()