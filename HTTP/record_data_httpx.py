import datetime
import hashlib
import json
import os
import os.path
import random
import string
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import httpx
import pymysql
import requests
from typing import List

from config import config
from log import record_log as log


def request_record_data(start_date: str, end_date: str) -> list:
    """
    请求呼叫中心接口数据
    :param start_date: 开始日期，yyyy-mm-dd
    :param end_date: 结束日期，yyyy-mm-dd
    :return: 数据列表
    """
    url: str = config["HTTP"]["DATA_REQUEST_URL"]
    token_url: str = config["HTTP"]["TOKEN_ACCESS_URL"]
    page_size: str = config["HTTP"]["PAGE_SIZE"]
    # 测试时启用

    # url = 'http://gateway.clmp-uat.csleasing.com.cn/hitf/v1/rest/invoke?namespace=HZERO
    # &serverCode=CCUZ.CENTER.CALL&interfaceCode=clmp-customize.udeskcallcentercalllog.queryAllType'
    # token_url = 'http://gateway.clmp-dev.csleasing.com.cn/oauth/oauth/token?
    # grant_type=client_credentials&client_secret=clcms-secret&client_id=clcms-client'
    try:
        access_token = 'Bearer ' + json.loads(
            httpx.post(token_url, headers={'Content-type': 'application/x-www-form-urlencoded'},
                       timeout=40).text)['access_token']

        # TODO 需要进行分页处理下载
        resp = httpx.post(url, json={
            "pathVariableMap": {
                "organizationId": 0
            },
            "requestParamMap": {
                "startingTime": start_date,
                "stopTime": end_date,
                "pageSize": page_size,
            },
        }, headers={'Authorization': access_token}, timeout=40)
        # 似乎不需要replace \\
        r: dict = json.loads(resp.text)
        receive_data = []  #
        if str(r["status"]) == "200":
            receive_data: list = json.loads(r["payload"])["content"]
            total_pages = int(json.loads(r["payload"])["totalPages"])
            total_elements = int(json.loads(r["payload"])["totalElements"])
            if total_pages > 1:
                for start_page in range(2, total_pages+1):
                    resp2 = httpx.post(url, json={
                        "pathVariableMap": {
                            "organizationId": 0
                        },
                        "requestParamMap": {
                            "startingTime": start_date,
                            "stopTime": end_date,
                            "startPage": start_page,
                            "pageSize": page_size,
                        },
                    }, headers={'Authorization': access_token}, timeout=40)
                    # 似乎不需要replace \\
                    r2: dict = json.loads(resp2.text)
                    receive_data.extend(json.loads(r2["payload"])["content"])

            log.info(f"获取录音记录列表成功, 实际共获取 [{len(receive_data)}]条记录, 工分 {total_pages} 页数据, "
                     f"接口共 {total_elements}条记录")
            # for data in receive_data_raw:
            #     item = dict(
            #
            #     )

        else:
            log.error(f"请求录音记录返回了错误的提示信息, 错误码: {r['status']}")
            receive_data = []

        # 格式化数据
        # for data in receive_data_raw:
        #     receive_data.append(dict(
        #         record_id=data['call_id'],  # 录音id
        #         start_time=data['startTime'],  # 通话开始时间
        #         end_time=data['endTime'],  # 通话结束时间
        #         call_no=data['CallNo'],  #
        #     ))

        """
        示例
        [{
            "appointid": 33036, 
            "callID": "1625470045.244822",
            "conversationId": null,
            "timestamp": "2021-07-05 15:27:39",
            "nickName": null,
            "customerPhone": "15275589622",
            "mobileArea": null,
            "displayNumber": null,
            "workflow": "dialout",
            "fromAgentId": null,
            "callResult": "dealing",
            "isLeavellessage": null,
            "totalTime": 114,
            "recordUrl": "http://10.25.7.100:8990/monitor/1.2.136.101/20210705/20210705-152726 N000000011288 15275589622 
            915275589622 1625470045.244822.mp3",
            "survey": null,
            "outlinePhoneNumber": null,
            "agentId": 8002,
            "customerRingAt": null,
            "customerAnswerAt": null,
            "agentAnswerAt": null,
            "pullRecordUrls": "http://minio-7c27d1.camp-uat-upgrade:9000/hzero-hzero-public/0
            /b7b735d91675483a9766c267aa6db191@hollyCrm-1625470045.244822.mp3",
        }]
        
        """
        return receive_data
    except Exception as exc:
        log.error(f"请求第三方接口失败, 请检查接口包含token获取接口是否正常, \n 错误提示: {exc}")
        return []

    # app_id = "qualityclient"
    # app_secret = "BzVSUmeY2FRzx8Jf791d3wSGdR2FkyGfi0"
    # nonce = ''.join(random.sample(string.ascii_letters + string.digits, 32))
    # t = int(time.time())
    # sign_str = f"Appid={app_id}&AppSecret={app_secret}&Nonce={nonce}&Time={t}"
    # sign = hashlib.md5(sign_str.encode(encoding='UTF-8')).hexdigest().upper()
    # data = {
    #     "startTime": start_date,
    #     "endTime": end_date,
    #     "Appid": app_id,
    #     "Nonce": nonce,
    #     "Time": t,
    #     "Sign": sign
    # }
    # resp = requests.post(url, json=data)  # 请求requests数据
    # data_receive = resp.json()
    # if data_receive["code"] != "0":
    #     log.error(f"录音数据请求失败 {data_receive}")
    #     return None
    # log.info(f"录音数据请求成功，数据量：{len(data_receive['Data'])}")
    # return data_receive["Data"]


# TODO 获取业务数据
def request_business_data(phone: str = '', start_time: str = '', end_time: str = '', business_type: str = '',
                          agent_name: str = '') -> list:
    """
    请求语音质检接口
    根据 客户号码, 通话时间, 坐席ID, 业务类型来获取业务数据, 并追加到通话记录数据中
    :param start_time: 通话开始时间 格式: yyyy-mm-dd
    :param end_time:  通话结束时间 格式: yyyy-mm-dd
    :param phone:
    :param business_type: 共三种 客服：CUSTOMER_SERVICE, 信审：CREDIT_REVIEW, 催收：COLLECTION
    :param agent_name: 坐席姓名
    :return:
    """
    qc_url = config["HTTP"]["RECORD_QC_URL"]
    try:
        # httpx默认5秒会超时, 但是请求接口时可能会超过5秒
        resp = httpx.post(qc_url, json={
            'phoneNo': phone,
            'businessType': business_type,
            'customerServiceName': agent_name,
            'dialBeginDate': start_time,
            'dialEndDate': end_time
        }, timeout=40)

        result = json.loads(resp.text)
        if result['respCode'] == '0000':
            business_data = result['data']['voiceQualityInspectionList']
            log.info(f"获取录音质检业务数据成功, 录音数据: {business_data}, result: {result}")
        else:
            business_data = []
            log.error(f"接口返回了错误的状态码, 状态码: {result['respCode']}, 状态错误提示: {result['respMsg']}")
    except httpx.ReadTimeout as exc:
        log.error("接口返回超时")
        business_data = []

    except Exception as exc:
        log.error(f'获取录音质检业务数据失败, 请确认接口通信是否正常. \n错误提示: {exc}')
        business_data = []

    return business_data


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


def download_record_old(record_and_path: str) -> dict:
    """
    下载单个录音
    :param record_and_path:
    :param record: 呼叫中心接口返回的语音列表中的一条记录
    :return: 赋值record_path后的语音记录
    """
    record, record_path = record_and_path
    # url_prefix = config["HTTP"]["RECORD_URL"]
    url = record["fileName"].replace('\\', '/')
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


def download_record(remote_path: str, local_path: str) -> int:
    """
    将远程文件下载到本地, 并返回状态 如果失败则重新下载
    :param remote_path:
    :param local_path:
    :return: 1: 成功, 0, 失败
    """
    try:
        file = httpx.get(url=remote_path, verify=False).content
        with open(local_path, 'wb') as f:
            f.write(file)
        status = 1
        log.info(f"录音文件下载成功: {remote_path}")
    except Exception as exc:
        log.error(f"录音下载失败: {remote_path}\n错误提示: {exc}")
        status = 0

    return status


def err_handler(request, exception):
    log.error(f"推送失败：{exception}")


def lower_key(data_list):
    """
    将字段名转小写
    """
    new_data_list = []
    for data in data_list:
        new_data = {}
        for key, value in data.items():
            new_data[key.lower()] = value
        new_data_list.append(new_data)
    return new_data_list


def data_serializer(data: dict) -> dict:
    """
    将对方接口数据序列化为标准化接口数据 task_info
    :param data: task_info
    :return:
    """
    new_data = dict(
        data_type='',
        data_treatment='',
        data_channel='',
        accesskey_id='',
        secret='',
        if_convert='',
        task_info='',
    )
    return new_data


def push_datareceive(data_list):
    """
    推送内部接口
    :param data_list: 符合规范的数据列表
    """
    fail_count = 0
    for data in data_list:
        log.info(f"推送数据量：{len(data['task_info'])}")
        resp = httpx.post(url=config["HTTP"]["DATA_RECEIVE_URL"], json=data, timeout=40)
        log.info(resp.json())
        if resp.json().get('CODE') != 20:
            fail_count += 1
    requests_count = len(data_list)
    log.info(f"数据推送完毕，总请求数：{requests_count}，成功 {requests_count - fail_count} 条，"
             f"失败 {fail_count} 条")


def request_datareceive(data_list):
    """
    推送内部接口
    :param data_list: 符合规范的数据列表
    """
    fail_count = 0
    log.info(f'推送任务将分: {len(data_list)}次推送')
    for data in data_list:
        log.info(f"推送数据量：{len(data['task_info'])}, 数据详情: {data['task_info']}")
        resp = httpx.post(config["HTTP"]["DATA_RECEIVE_URL"], json=data, timeout=40)
        log.info(resp.json())
        if resp.json().get('CODE') != 20:
            fail_count += 1
    requests_count = len(data_list)
    log.info(f"数据推送完毕，总请求数：{requests_count}，成功 {requests_count - fail_count} 条，"
             f"失败 {fail_count} 条")


def start_request_data(date=None):
    """
    通过定时器调用该任务
    :return: 包含原生录音数据 和业务数据 并下载录音和更新了下载地址
    """
    # 获取当前时间日期
    yesterday = datetime.datetime.today() + datetime.timedelta(-1)
    # start_time = yesterday.strftime('%Y-%m-%d') + ' ' + '00:00:00'

    # 根据日期手动补数 格式: YYYY-mm-dd
    if date:
        start_time = date + ' ' + '00:00:00'
        end_time = date + ' ' + '23:59:59'
        local_record_path_prefix = os.path.join(config['PREFIX_PATH'], date)

    else:
        start_time = yesterday.strftime('%Y-%m-%d') + ' ' + '00:00:00'
        end_time = yesterday.strftime('%Y-%m-%d') + ' ' + '23:59:59'
        local_record_path_prefix = os.path.join(config['PREFIX_PATH'], yesterday.strftime('%Y-%m-%d'))

    # 根据当前时间获取最近一天的录音通话记录数据
    receive_data = request_record_data(start_time, end_time)
    log.info(f"正在获取日期: {start_time[:10]}的数据, 共 {len(receive_data)} 条, 请求随录数据成功: {receive_data}, ")

    # 格式化随录数据

    data_list = []  # 保存序列化后的数据

    # 下载录音文件并更新录音地址 更新数据

    for data in receive_data:

        # remote_record_path: str = data['pullRecordUrls']  # 录音下载地址
        # TODO 当录音文件不存在时需要处理
        if data['pullRecordUrls'] and data['callResult'] == 'dealing':
            remote_record_path: str = data['pullRecordUrls']
            # .replace(
            #     'http://minio-7c27d1.camp-uat-upgrade:9000', 'http://10.18.110.120:30200').replace(
            #     'http://minio-h0uat.csleasing.com.cn', 'http://10.18.110.120:30200')  # 录音下载地址
            # 示例 http://minio-7c27d1.camp-uat-upgrade:9000 \
            # /hzero-hzero-public/0/b7b735d91675483a9766c267aa6db191@hollyCrm-1625470045.244822.mp3

            # TODO 获取数据类型
            # TODO 确定业务类型规则  根据坐席所属部门确定业务类型
            log.info(f"坐席所属部门: [{data['departmentName']}].")
            if data['departmentName'] == '风险管理部':
                business_type = 'CREDIT_REVIEW'  # 信审
            elif data['departmentName'] == '客户服务部':
                business_type = 'CUSTOMER_SERVICE'  # 客服
            elif data['departmentName'] == '资产管理部':
                business_type = 'COLLECTION'  # 催收
            # TODO 需要确定是否还有其他的部门名称或类型
            else:
                log.info(f"未识别的部门: {data['departmentName']}, 通话流水号: {data['callId']}")
                business_type = 'unknown'

            # 添加业务类型到字典
            data['business_type'] = business_type

            uid = str(uuid.uuid1()).replace('-', '')
            # 文件格式: 业务类型 + 日期 + uid + 通话ID
            file_name = f"{business_type}-{data['startTime'][:10].replace('-', '')}-{data['callId']}-{uid}" \
                        f".{remote_record_path.split('.')[-1]}"  # " \

            # TODO 按照 年-月-日/ call_uuid 存储数据
            # yesterday_date = yesterday.strftime('%Y-%m-%d')

            # local_record_path_prefix = os.path.join(config['PREFIX_PATH'], yesterday_date)
            if not os.path.exists(local_record_path_prefix):
                # 按照日期创建录音文件夹
                os.makedirs(local_record_path_prefix)

            local_record_path = os.path.join(local_record_path_prefix, file_name)

            # status = download_record(remote_record_path, local_record_path)

            #
            i = 0
            while i < 3:
                status = download_record(remote_record_path, local_record_path)
                if status:
                    # 下载成功
                    # TODO 更新录音地址
                    file_size = os.stat(local_record_path).st_size
                    if file_size == 0:
                        log.warning(f'录音文件为空, ')
                        status = -1  # 重置录音状态 不
                        data['record_path'] = local_record_path
                        data['record_uuid'] = uid
                        data['record_dl_flag'] = -1
                        record_dl_flag = -1
                    else:

                        log.info(f'通话流水号: {data["callId"]}, 录音文件下载成功,本地地址: {local_record_path}!')
                        data['record_path'] = local_record_path
                        data['record_uuid'] = uid
                        data['record_dl_flag'] = 1
                        record_dl_flag = 1
                    break

                else:
                    data['record_dl_flag'] = 0
                    record_dl_flag = 0
                    # 如果下载失败需要重试
                    i = i + 1
            pass

            # 查询业务字段
            if data['customerPhone'] and business_type and data['endTime'] and data['startTime']:
                # 根据呼叫类型和主被叫号码来判断客户号码
                if data['workflow'] == 'normal':
                    phone = data['callNo']
                elif data['workflow'] == 'dialout':
                    phone = data['customerPhone']
                else:
                    phone = data['customerPhone']

                business_data = request_business_data(
                    phone=phone,  # 填写客户号码
                    start_time=data['startTime'][:10],
                    end_time=data['endTime'][:10],
                    business_type=business_type,
                    agent_name=data['agentNickName']
                )

                # 将业务数据拼接到数据列表中
                # TODO 如果未匹配到业务数据的处理规则
                if len(business_data) > 0:
                    business_flag = 1
                else:
                    business_flag = -1
                data['business_data'] = business_data
            else:
                log.error(f"客户号码: {data['customerPhone']} 或 坐席所属部门: {data['departmentName']}未匹配业务类型")
                data['business_data'] = []
                business_flag = -2

            # 将新的data添加到 data_list
            # TODO 将任务处理状态添加到数据库
            with pymysql.connect(host=config['MYSQL']['host'],
                                 port=config['MYSQL']['port'],
                                 user=config['MYSQL']['user'],
                                 passwd=config['MYSQL']['passwd'],
                                 db=config['MYSQL']['db']
                                 ) as conn:
                with conn.cursor() as cur:
                    insert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    cur.execute("insert into records values "
                                "(default, %s, %s, %s, %s,"
                                "%s, %s, %s, %s, %s,"
                                "%s, %s, %s, %s, %s)", (data['record_dl_flag'], business_flag, data['callId'],
                                                        data['startTime'], insert_time, business_type,
                                                        data['callResult'], data['departmentName'],
                                                        data['customerPhone'],
                                                        data['agentNickName'], data['startTime'], data['endTime'],
                                                        data['workflow'], data['hanguper']))
                    log.info("插入数据库成功")
                conn.commit()

            if data['record_dl_flag'] == 1 and business_flag == 1:
                data_list.append(data)
            # TODO 下载失败的数据处理规则
            else:
                pass
        else:

            # TODO 需要添加到额外

            log.error("录音文件不存在!")
    log.info(f"昨日录音数据获取成功, 共{len(receive_data)}条, 成功获取录音文件{len(data_list)}条.")

    return data_list
    # # 推送数据到抽音内部接口
    # push_datareceive(data_list)
