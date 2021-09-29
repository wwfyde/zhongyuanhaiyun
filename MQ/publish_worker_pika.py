# !/usr/bin/env python
# -*- coding=utf-8 -*-


import time
import json
import pika
from datetime import datetime
import logging


class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Singleton, cls).__new__(cls)
        return cls._inst


class PublishWorker(Singleton):
    def __init__(self, config):
        self.channel = None
        self.host = config["QUEUE_HOST"]
        self.port = config["QUEUE_PORT"]
        self.user = config["QUEUE_USER"]
        self.pwd = config["QUEUE_PWD"]
        self.channel_conn()

    def channel_conn(self):
        """
        获取队列通道
        """
        while self.channel is None or self.channel.is_open == False:
            try:
                mq_conparm = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    socket_timeout=5,
                    credentials=pika.credentials.PlainCredentials(self.user, self.pwd),
                    heartbeat=600
                )
                mq_connection = pika.BlockingConnection(mq_conparm)
                self.channel = mq_connection.channel()
                return self.channel
            except BaseException as e:
                print("队列连接通道错误", e)
                time.sleep(5)
                self.channel = None

        return self.channel

    def serial_crm_data(self, crm_data):
        for key in crm_data.keys():
            crm_data[key] = self.json_serial(crm_data[key])
        return crm_data

    def json_serial(self, obj):
        if isinstance(obj, datetime):
            serial = str(obj)
            # serial = obj.isoformat()
            return serial
        else:
            return obj

    def send_data_queue(self, queue_name, crm_data):
        """
        :param queue_name:
        bj_high_queue  wh_high_queue  bj_low_queue wh_low_queue
        :param crm_data:
        :return:
        """
        send_data = None
        try:
            send_data = json.dumps(self.serial_crm_data(crm_data))
            # logging.info("json sent to queue" + str(send_data))
            channel = self.channel_conn()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=send_data,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                    content_encoding='utf-8',
                )
            )

        except BaseException as e:
            logging.exception("channel connection error......")
            self.channel = None
            self.send_data_queue(queue_name, crm_data)  # 用于rabbitmq服务断掉时处理当前数据的

    def get_queue_data(self, queue_name):
        try:
            channel = self.channel_conn()
            channel.queue_declare(queue=queue_name, durable=True)
            method_frame, header_frame, crm_data = channel.basic_get(queue=queue_name)
        except BaseException as e:
            self.channel = None
            channel = self.channel_conn()
            channel.queue_declare(queue=queue_name, durable=True)
            method_frame, header_frame, crm_data = channel.basic_get(queue=queue_name)
        if crm_data is not None:
            crm_data = json.loads(crm_data)
            self.delete_queue_data(method_frame)
        return crm_data

    def delete_queue_data(self, method_frame):
        try:
            if self.channel is not None:
                self.channel.basic_ack(method_frame.delivery_tag)  # 从队列中删除
        except BaseException as e:
            self.channel = None
            self.channel = self.channel_conn()
            self.channel.basic_ack(method_frame.delivery_tag)  # 从队列中删除

    def delete_queue(self, queue_name):
        channel = self.channel_conn()
        channel.queue_delete(queue=queue_name)

    def close(self):
        if self.channel is not None:
            self.channel.close()
