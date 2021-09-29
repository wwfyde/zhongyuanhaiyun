# !/usr/bin/env python
# -*- coding=utf-8 -*-


import json
import time
import traceback
import logging
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError


class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Singleton, cls).__new__(cls)
        return cls._inst

class Kafka_producer(Singleton):
    def __init__(self, kafkahost, kafkaport, kafkatopic):
        self.kafkaHost = kafkahost
        self.kafkaPort = kafkaport
        self.kafkatopic = kafkatopic
        self.producer = None
        self.get_producer()
        
    def get_producer(self):
        while self.producer is None:
            try:
                self.producer = KafkaProducer(bootstrap_servers='{kafka_host}:{kafka_port}'.format(
                    kafka_host=self.kafkaHost,
                    kafka_port=self.kafkaPort
                ))
            except BaseException:
                logging.exception("KafkaProducer FUNCTION init—BaseException:"+traceback.format_exc())
                time.sleep(5)
                self.producer = None
    
    def sendJsonData(self, params):
        try:
            parmas_message = json.dumps(params)
            producer = self.producer
            producer.send(self.kafkatopic, parmas_message.encode('utf-8'))
            producer.flush()
        except BaseException:
            logging.exception("KafkaProducer FUNCTION sendJsonData—BaseException:"+traceback.format_exc())
            self.producer = None
            self.get_producer()
            self.sendJsonData(params)
    
    def close(self):
        if self.producer is not None:
            try:
                self.producer.close()
            except BaseException:
                logging.exception("KafkaProducer FUNCTION close—BaseException:"+traceback.format_exc())

class Kafka_consumer(Singleton):
    '''
    使用Kafka—python的消费模块
    '''

    def __init__(self, kafkahost, kafkaport, kafkatopic, groupid):
        self.kafkaHost = kafkahost
        self.kafkaPort = kafkaport
        self.kafkatopic = kafkatopic
        self.groupid = groupid
        self.consumer = None
        self.get_consumer()
        
    def get_consumer(self):
        while self.consumer is None:
            try:
                self.consumer = KafkaConsumer(group_id=self.groupid,
                                              bootstrap_servers='{kafka_host}:{kafka_port}'.format(
                                                  kafka_host=self.kafkaHost,
                                                  kafka_port=self.kafkaPort))
                self.consumer.subscribe(topics=(self.kafkatopic,))
            except BaseException:
                logging.exception("KafkaConsumer FUNCTION init—BaseException:"+traceback.format_exc())
                time.sleep(0.1)
                self.consumer = None
        
    def getJsonDataList(self,list_size=1):
        try:
            msg = self.consumer.poll(timeout_ms=500, max_records=list_size)
            if msg and len(msg.keys()) > 0:
                result = []
                for v in list(msg.values())[0]:
                    result.append(json.loads(v.value))
                return result
            return None
        except BaseException:
            logging.exception("KafkaConsumer FUNCTION getJsonData—BaseException:"+traceback.format_exc())
            self.consumer = None
            self.get_consumer()
            return self.getJsonData()
    
    def close(self):
        if self.consumer is not None:
            try:
                self.consumer.close()
            except BaseException:
                logging.exception("KafkaConsumer FUNCTION close—BaseException:"+traceback.format_exc())

if __name__ == '__main__':
    ##################producer########################
    producer = Kafka_producer("127.0.0.1", 9092, "test")
    for i in range(10):
        params = {"key"+str(i):'test---' + str(i)}
        print(str(i)+"->send data:"+str(params))
        producer.sendJsonData(params)
        time.sleep(0.1)
    producer.close()
    #################consumer#######################
    consumer = Kafka_consumer('127.0.0.1', 9092, "test", 'test-python-test')
    msg = consumer.getJsonDataList(20)
    print(str(i)+"->get data:"+str(type(msg))+"<-->"+str(len(msg))+"<-->"+str(msg))
    consumer.close()