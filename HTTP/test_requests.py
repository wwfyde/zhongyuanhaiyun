# coding=utf-8

import json
import requests
import os
import logging
import traceback


def http_post(url, data):
    try:

        headers = {'Content-Type': 'application/json'}

        response = requests.post(url=url, headers=headers, data=json.dumps({'data': data}))
        res = response.text

        return json.loads(res)
    except:
        print("post error:", os.path.abspath(__file__))
        logging.exception(traceback.format_exc())
        return None


if __name__ == "__main__":
    url = 'http://127.0.0.1:9000/msg/'

    content = {"begin_date": "2020-07-04 00:00:00", "end_date": "2020-07-04 23:59:59"}

    res = http_post(url, content)

    print(res)
