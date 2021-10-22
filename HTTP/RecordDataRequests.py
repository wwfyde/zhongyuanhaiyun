import datetime
import hashlib
import os
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import requests
from config import config
from log import record_log as log


def request_data(start_date, end_date):
    """
    请求呼叫中心接口数据
    :param start_date: 开始日期，yyyy-mm-dd
    :param end_date: 结束日期，yyyy-mm-dd
    :return: 数据列表
    """
    url = config["HTTP"]["DATA_REQUEST_URL"]
    app_id = "qualityclient"
    app_secret = "BzVSUmeY2FRzx8Jf791d3wSGdR2FkyGfi0"
    nonce = ''.join(random.sample(string.ascii_letters + string.digits, 32))
    t = int(time.time())
    sign_str = f"Appid={app_id}&AppSecret={app_secret}&Nonce={nonce}&Time={t}"
    sign = hashlib.md5(sign_str.encode(encoding='UTF-8')).hexdigest().upper()
    data = {
        "startTime": start_date,
        "endTime": end_date,
        "Appid": app_id,
        "Nonce": nonce,
        "Time": t,
        "Sign": sign
    }
    resp = requests.post(url, json=data)
    data_receive = resp.json()
    if data_receive["code"] != "0":
        log.error(f"录音数据请求失败 {data_receive}")
        return None
    log.info(f"录音数据请求成功，数据量：{len(data_receive['Data'])}")
    return data_receive["Data"]


def create_record_path():
    """
    创建录音文件夹
    :return:
    """
    record_path = os.path.abspath(config["HTTP"]["RECORD_PATH"])
    yesterday = (datetime.date.today() + datetime.timedelta(days=-1)).strftime('%Y%m%d')
    record_path = os.path.join(record_path, yesterday)
    if not os.path.isdir(record_path):
        os.makedirs(record_path)
    return record_path


def download_record(record_and_path):
    """
    下载单个录音
    :param record: 呼叫中心接口返回的语音列表中的一条记录
    :return: 赋值record_path后的语音记录
    """
    record, record_path = record_and_path
    url_prefix = config["HTTP"]["RECORD_URL"]
    url = url_prefix + record["fileName"].replace('\\', '/')
    record["fileName"] = record["fileName"].replace('\\', '')
    try:
        resp = requests.get(url)
        record_path = os.path.join(record_path, record["fileName"])
        with open(record_path, 'wb') as f:
            f.write(resp.content)
        record["record_path"] = record_path
        log.info(f"录音下载成功：{url}")
    except Exception as e:
        log.error(f"录音下载失败：{url}\n{e}")
        record["record_path"] = ""
    return record


def download_record_batch(data_list):
    """
    批量下载录音
    :param data_list: 呼叫中心接口返回的语音列表
    :return: 赋值record_path后的语音列表
    """
    record_path = create_record_path()
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=10) as pool:
        tasks = [pool.submit(download_record, (data, record_path)) for data in data_list]
        record_list = [future.result() for future in as_completed(tasks)]
    t2 = time.time()
    log.info(f"共 {len(record_list)} 条录音文件，已下载 {len([1 for data in record_list if data['record_path']])} 条录音文件，"
             f"耗时 {t2-t1}s")
    return record_list


def err_handler(request, exception):
    log.error(f"推送失败：{exception}")


def request_datareceive(data_list):
    """
    推送内部接口
    :param data_list: 符合规范的数据列表
    """
    fail_count = 0
    for data in data_list:
        log.info(f"推送数据量：{len(data['task_info'])}")
        resp = requests.post(config["HTTP"]["DATA_RECEIVE_URL"], json=data)
        log.info(resp.json())
        if resp.json().get('CODE') != 20:
            fail_count += 1
    requests_count = len(data_list)
    log.info(f"数据推送完毕，总请求数：{requests_count}，成功 {requests_count - fail_count} 条，"
             f"失败 {fail_count} 条")
