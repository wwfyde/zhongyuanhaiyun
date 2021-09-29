# !/usr/bin/env python
# -*- coding=utf-8 -*-


import time
import traceback
import logging
from kombu import Connection

class Singleton(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Singleton, cls).__new__(cls)
        return cls._inst


class PublishWorker(Singleton):

    def __init__(self, c_host, c_port, c_user, c_pwd):
        self.conn = None
        self.host = c_host
        self.port = c_port
        self.user = c_user
        self.pwd = c_pwd
        self.channel_conn()

    def channel_conn(self):
        """
        获取队列通道
        """
        while self.conn is None:
            try:
                url = 'amqp://%s:%s@%s:%s//' % (self.user, self.pwd, self.host, self.port)
                conn = Connection(url)
                self.conn = conn
                return self.conn
            except BaseException:
                print("队列连接通道错误")
                logging.exception("PublishWorker FUNCTION channel_conn—BaseException:" + traceback.format_exc())
                time.sleep(5)
                self.conn = None

        return self.channel
    
    def send_data_queue(self, queue_name, crm_data):
        """
        :param queue_name:
        bj_high_queue  wh_high_queue  bj_low_queue wh_low_queue
        :param crm_data:
        :return:
        """
        try:
            if self.conn is None:
                self.channel_conn()
            
            simple_queue = self.conn.SimpleQueue(queue_name)
            simple_queue.put(crm_data)
            simple_queue.close()
        except BaseException:
            logging.exception("PublishWorker FUNCTION send_data_queue—BaseException:" + traceback.format_exc())
            self.conn = None
            self.send_data_queue(queue_name, crm_data)  #  用于rabbitmq服务断掉时处理当前数据的

    def get_queue_data(self, queue_name):
        result = None
        try:
            if self.conn is None:
                self.channel_conn()
            
            simple_queue = self.conn.SimpleQueue(queue_name)
            
            if simple_queue.qsize() > 0:
                msg = simple_queue.get(block=True, timeout=100)
                result = msg.payload
                msg.ack()
        except BaseException:
            try:
                self.conn = None
                self.channel_conn()
                simple_queue = self.conn.SimpleQueue(queue_name)
                if simple_queue.qsize() > 0:
                    msg = simple_queue.get(block=True, timeout=500)
                    result = msg.payload
                    msg.ack()
            except BaseException:
                logging.exception("PublishWorker FUNCTION get_queue_data—BaseException:" + traceback.format_exc())
        
        return result
    
    def close(self):
        if self.conn is not None:
            self.conn.close()


if __name__ == '__main__':
    public = PublishWorker('127.0.0.1', 5672, 'sks', '123')
    print("send msg:" + str({'key':'test1'}))
    public.send_data_queue('test', {'key':'test1'})
    print("get msg:" + str(public.get_queue_data('test')))
    
