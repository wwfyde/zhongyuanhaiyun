#coding=utf-8

import json
import grequests
import time

def err_handler(request, exception):
    print("请求出错",exception)
    
def test_web():
    
    words = ["中国","北京","你好","奥运","七夕","2022","大盘","向往的生活","茅台"]
    
    urls = ["https://www.baidu.com/sugrec?prod=pc&wd={word}&cb=".format(word=wd) for wd in words]
    
    req_list = [grequests.get(url) for url in urls]
    t1 = time.time()
    res_list = grequests.map(req_list, exception_handler=err_handler,size=1)
    t2 = time.time()
    print('test_dbpool', t2 - t1)
    
    for i in res_list:
        res = json.loads(i.text[1:-1])
        rsp = [r["q"] for r in res['g']]
        print(res["q"],"===>>",rsp)

if __name__ == '__main__':
    test_web()
    