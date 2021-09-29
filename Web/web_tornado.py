#coding=utf-8

import json

import traceback
import logging

import tornado.web
import tornado.ioloop

class IndexHandler(tornado.web.RequestHandler):
    """主路由处理类"""
    def post(self):
        try:
            dict = json.loads(self.request.body)
            logging.info("param:"+str(dict))
        except BaseException:
            logging.exception("IndexHandler FUNCTION post:"+traceback.format_exc())
    
        templateStr = {"result":"sucess"}
        self.write(templateStr)
 
if __name__ == '__main__':
    app = tornado.web.Application([
          (r"/sql/event/", IndexHandler),
      ])
    app.listen(9000)
    tornado.ioloop.IOLoop.current().start()
