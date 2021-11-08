import json
import os
import sys
from math import ceil

import httpx

# 通过MySQL数据库导入
from DB.mysql_base import MysqlBase
from HTTP.record_data_httpx import start_request_data
from MQ.publish_worker_pika import PublishWorker
from config import config
from HTTP.record_data_httpx import request_datareceive
from log import record_log as log


# 该接口报废
def get_data_from_http(start_date: str, end_date: str) -> list:
    """
    查询第三方接口
    :param start_date:
    :param end_date:
    :return:
    """
    url = config["HTTP"]["DATA_REQUEST_URL"]  # 随录接口请求地址

    # 请求数据
    data = {

    }
    httpx.post(url=url, json=data)

    return []


def get_data_from_mysql(start_date, end_date):
    """
    查询mysql数据库
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return:
    """
    mysql_base = MysqlBase()
    mysql_base.init(config["MYSQL"])
    data_list = mysql_base.select_sql(config["SQL"]["record_sql"], (start_date, end_date))
    log.info(f"从数据库中取得 {len(data_list)} 条数据")
    mysql_base.close()
    return data_list


def get_data_from_queue():
    """
    从队列中获取全部的任务数据
    """
    publish = PublishWorker(config["QUEUE"])
    data = publish.get_queue_data(config["QUEUE"]["QUEUE_NAME"])
    publish.close()
    return data['data_list'] if data else []


def get_data_from_file(date, file_name):
    """
    从本地文件获取数据
    :param file_name: 数据文件名
    :param date: yyyy-mm-dd
    """
    # 指定日期手动执行，从文件中读取数据
    local_path = os.path.join(config["HTTP"]["DATA_PATH"], date, file_name)
    if not os.path.isfile(local_path):
        log.info(f"文件不存在：{local_path}")
        sys.exit()
    data_list = []
    with open(local_path) as records_file:
        for record in records_file:
            data_list.append(json.loads(record))
    log.info(f"从 {file_name} 中读取 {len(data_list)} 条数据")
    return data_list


def parse_path(data_list):
    """
    处理录音路径字段，修改为绝对路径，排除空路径数据
    返回处理后的数据列表，及无对应录音文件的数据列表
    """

    # TODO 可能需要注意一下, 录音文件目录结构的问题
    new_data_list = []
    failed_data_list = []
    total_record_path_list = []
    date_time = data_list[0].get("answer_time")
    year = date_time[0:4]
    month = date_time[5:7]
    day = date_time[8:10]
    base_record_path = os.path.join(config["PREFIX_PATH"], year, month, day)
    log.info(f"在目录 {base_record_path} 下搜索录音文件...")
    sub_record_path_list = [os.path.join(base_record_path, path) for path in os.listdir(base_record_path)]
    for sub_record_path in sub_record_path_list:
        total_record_path_list.extend([os.path.join(sub_record_path, path) for path in os.listdir(sub_record_path)])
    for data in data_list:
        if data.get("calluuid"):
            # 根据数据列表查找相关的录音文件
            record_path_list = [path for path in total_record_path_list if data["calluuid"] in path]
            if record_path_list:
                if len(record_path_list) > 1:
                    log.warning("当前业务含有多个录音文件，connid："+data.get("connid"))
                data["record_path"] = record_path_list[0]
                new_data_list.append(data)
            else:
                log.warning(f"当前业务不存在对应的录音文件，connid：{data.get('connid')}，calluuid：{data.get('calluuid')}")
                failed_data_list.append(data)

    return new_data_list, failed_data_list


# TODO 根据实际情况情况确认是否需要映射字段
def mapping_fields(data_list):
    """
    字段值映射及其他处理
    """
    for data in data_list:
        if data.get("cde_call_type") == 1 or data.get("cde_call_type") == '1':
            data["cde_call_type"] = "内部呼叫"
        elif data.get("cde_call_type") == 2 or data.get("cde_call_type") == '2':
            data["cde_call_type"] = "呼入"
        elif data.get("cde_call_type") == 3 or data.get("cde_call_type") == '3':
            data["cde_call_type"] = "呼出"
        if data.get("cde_release_code") == "1 local":
            data["cde_release_code"] = "坐席挂机"
        elif data.get("cde_release_code") == "2 remote":
            data["cde_release_code"] = "客户挂机"
        if data.get("cde_call_type") in ("呼入", "呼出"):
            data["call_direction"] = data["cde_call_type"]
        elif data.get("employeeid"):
            data["call_direction"] = "呼入"
        elif data.get("employeeid_from"):
            data["call_direction"] = "呼出"


# TODO 序列化接口数据
def generate_data_1(data_list):
    """
    生成符合接口规范的数据, 并且子列表每条最大1000条数据
    """
    task_info = []
    for item in data_list:
        data, record_info = {}, {}
        record_data = item.copy()
        if len(item['business_data']):
            business_data: dict = item['business_data'][0].copy()  # 获取业务数据中的第一条

            # TODO 将未序列化的数据页添加到字典
            # record_info = item.copy()

            # 录音字典定制数据
            record_info["record_id"] = record_data["callId"]  # 通话流水号
            record_info['record_path'] = record_data['record_path']  # 本地录音地址
            record_info["record_time"] = record_data["timestamp"]  # 录音开始时间
            record_info["record_flag"] = '0'  # 录音状态标记
            record_info['customer_phone'] = record_data['customerPhone']  # 客户电话
            record_info['workflow'] = record_data['workflow']  # 通话流程 in: 呼入
            record_info['call_result'] = record_data['callResult']  # 通话结果
            record_info['agent_id'] = record_data['agentId']  # 客服ID
            record_info['agent_name'] = record_data['agentNickName']  # 客服名称
            record_info['relevant_agent'] = record_data['relevantAgent']  # 相关客服
            record_info['call_no'] = record_data['callNo']  # 主叫号码
            record_info['start_time'] = record_data['startTime']  # 通话开始时间
            record_info['end_time'] = record_data['endTime']  # 通话结束时间
            record_info['supplier_type'] = record_data['supplierType']  # 供应商类型
            record_info['call_state'] = record_data['callState']  # 事件状态
            record_info['department_name'] = record_data['departmentName']  # 坐席所属部门
            record_info['business_type'] = record_data['business_type']  # 业务类型
            record_info['hanguper'] = record_data['hanguper']  # 主叫方

            # 构造业务字段
            data["task_id"] = record_data["callId"]  # 任务流水号
            data["record_list"] = record_data["callId"]  # 录音列表
            data["task_time"] = record_data["timestamp"]  # 任务时间
            data["task_flag"] = '0'  # 任务标记 用于后续处理过程状态迁移标记

            # 业务字典定制数据
            data['order_no'] = business_data['orderNo']  # 订单编号
            data['contract_no'] = business_data['contractNo']  # 合同编号
            data['product_name'] = business_data['productName']  # 产品方案/产品信息
            data['customer_name'] = business_data['customerName']  # 客户姓名
            data['customer_phone'] = business_data['customerPhoneNo']  # 客户电话
            data['apply_time'] = business_data['applyTime']  # 申请时间
            data['business_type'] = business_data['businessTypeDesc']  # 业务类型 : 信审/客服/催收
            data['marriage_status'] = business_data['marriageStatusDesc']  # 婚姻状况
            data['contact_name'] = business_data['contactNameDesc']  # 联系名称
            data['dealer_no'] = business_data['dealerNo']  # 经销商代码
            data['dealer_name'] = business_data['dealerName']  # 经销商名称
            data['dealer_abbr'] = business_data['dealerAbbreviationName']  # 经销商简称
            data['prequalification_level'] = business_data['prequalificationLevel']  # 预审批等级
            data['credit_review_result'] = business_data['creditReviewResult']  # 信审决策结果
            data['final_approval_result'] = business_data['finalApprovalResult']  # 最终审批结果
            data['handle_time'] = business_data['handleTime']  # 处理时间
            data['application_status'] = business_data['applicationStatusDesc']  # 申请状态描述
            data['customer_problems'] = business_data['customerProblems']  # 客户问题

            # 设置与任务相关的录音信息列表
            data["record_info"] = [record_info]  # 构造录音字段数据
            task_info.append(data)
        else:
            log.error("录音质检接口数据未匹配, 将不会推送到抽音数据库")
    log.info(f"已生成 {len(task_info)} 条任务数据")
    # 将task_info数据列表按照 SEND_SIZE 配置项分割成多个部分
    send_size = config["HTTP"]["SEND_SIZE"]
    # 将一个大列表拆分成子列表最多1000个的小列表
    task_info_sep = [task_info[i * send_size:(i + 1) * send_size] for i in
                     range(ceil(len(task_info) / send_size))]
    # 生成接口数据
    data_tmpl = {
        "data_type": "speech",
        "data_treatment": "batch",
        "data_channel": "zyhy",  # TODO zyhy 录音转码命令中需要用到
        "accesskey_id": "asdf",
        "secret": "123456",
        "if_convert": "yes"
    }
    data_list = []
    for task_info in task_info_sep:
        data = data_tmpl.copy()
        data["task_info"] = task_info
        data_list.append(data)
    return data_list


def generate_data(data_list):
    """
    生成符合接口规范的数据, 并且子列表每条最大1000条数据
    """
    task_info = []
    for item in data_list:
        data, record_info = {}, {}
        record_data = item.copy()
        # TODO 将未序列化的数据页添加到字典
        record_info = item.copy()
        # 录音字典定制数据
        record_info["record_id"] = record_data["callId"]  # 通话流水号
        record_info['record_path'] = record_data['record_path']  # 本地录音地址
        record_info["record_time"] = record_data["timestamp"]  # 录音开始时间
        record_info["record_flag"] = '0'  # 录音状态标记


        data['customer_phone'] = record_data['customerPhone']  # 客户电话
        data['workflow'] = record_data['workflow']  # 通话流程 in: 呼入
        data['call_result'] = record_data['callResult']  # 通话结果
        data['agent_id'] = record_data['agentId']  # 客服ID
        data['agent_name'] = record_data['agentNickName']  # 客服名称
        data['relevant_agent'] = record_data['relevantAgent']  # 相关客服
        data['call_no'] = record_data['callNo']  # 主叫号码
        data['start_time'] = record_data['startTime']  # 通话开始时间
        data['end_time'] = record_data['endTime']  # 通话结束时间
        data['supplier_type'] = record_data['supplierType']  # 供应商类型
        data['call_state'] = record_data['callState']  # 事件状态
        data['department_name'] = record_data['departmentName']  # 坐席所属部门
        data['business_type'] = record_data['business_type']  # 业务类型
        data['hanguper'] = record_data['hanguper']  # 主叫方

        # 构造业务字段
        data["task_id"] = record_data["callId"]  # 任务流水号
        data["record_list"] = record_data["callId"]  # 录音列表
        data["task_time"] = record_data["timestamp"]  # 任务时间
        data["task_flag"] = '0'  # 任务标记 用于后续处理过程状态迁移标记

        # 设置与任务相关的录音信息列表
        data["record_info"] = [record_info]  # 构造录音字段数据
        task_info.append(data)
    log.info(f"已生成 {len(task_info)} 条任务数据")
    # 将task_info数据列表按照 SEND_SIZE 配置项分割成多个部分
    send_size = config["HTTP"]["SEND_SIZE"]
    # 将一个大列表拆分成子列表最多1000个的小列表
    task_info_sep = [task_info[i * send_size:(i + 1) * send_size] for i in
                     range(ceil(len(task_info) / send_size))]
    # 生成接口数据
    data_tmpl = {
        "data_type": "speech",
        "data_treatment": "batch",
        "data_channel": "zyhy",  # TODO zyhy 录音转码命令中需要用到
        "accesskey_id": "asdf",
        "secret": "123456",
        "if_convert": "yes"
    }
    data_list = []
    for task_info in task_info_sep:
        data = data_tmpl.copy()
        data["task_info"] = task_info
        data_list.append(data)
    return data_list

def err_handler(request, exception):
    log.error("请求出错", exception)
    sys.exit()


def write_to_failed_records(data_list, local_path):
    """
    将无对应录音文件的数据持久化到文件中 failed_records.txt
    :param data_list: 录音数据列表 [{},{}]
    :param local_path: failed_records.txt文件所在路径
    """
    file_path = os.path.join(local_path, 'failed_records.txt')
    with open(file_path, 'a', encoding='utf-8') as failed_records:
        for data in data_list:
            failed_records.write(json.dumps(data, ensure_ascii=False) + '\n')
    return file_path


# TODO 程序入口
def start_capture(append_date=None):
    """
    获取队列数据
    生成指定格式数据，推送 datarecieve 接口
    :param append_date: 手动补数据日期，yyyy-mm-dd
    """
    try:
        log.info("开始录音数据获取及推送")
        if not append_date:
            # 自动取数
            # TODO 直接在该位置读取数据 调用httpx 不需要额外再创建定时任务了
            # data_list = get_data_from_queue()
            data_list = start_request_data()  # 获取到的
        else:
            # 手动补数
            data_list = get_data_from_file(append_date, 'total_records.txt')
        if not data_list:
            log.info("无数据需要推送，程序结束...")
            return
        log.info(f"获取数据量：{len(data_list)}")
        # record_list, failed_data_list = parse_path(data_list)
        # log.info(f"滤除空路径后的数据量：{len(record_list)}")
        # log.info(f"无对应录音文件的数据量：{len(failed_data_list)}")
        # if failed_data_list:
        #     local_path = os.path.join(config["HTTP"]["DATA_PATH"], failed_data_list[0]["answer_time"][:10])
        #     if not os.path.exists(local_path):
        #         os.makedirs(local_path)
        #     file_path = write_to_failed_records(failed_data_list, local_path)
        #     log.info(f'写入 {len(failed_data_list)} 条数据到 {file_path} 文件中')
        if not data_list:
            log.info("不存在有录音文件的数据，程序结束...")
            return
        # mapping_fields(data_list)  # TODO 是否需要映射字段
        data_list = generate_data(data_list)
        request_datareceive(data_list)
    except Exception as e:
        log.error("抽音程序异常")
        log.error(e, exc_info=1)


def append_failed(date):
    """
    推送失败的数据
    :param date: yyyy-mm-dd
    """
    try:
        log.info("开始重推失败数据")
        data_list = get_data_from_file(date, "failed_records.txt")
        if not data_list:
            log.info("无数据需要推送，程序结束...")
            return
        log.info(f"获取数据量：{len(data_list)}")
        record_list, failed_data_list = parse_path(data_list)
        log.info(f"滤除空路径后的数据量：{len(record_list)}")
        log.info(f"无对应录音文件的数据量：{len(failed_data_list)}")
        if not record_list:
            log.info("不存在有录音文件的数据，程序结束...")
            return
        mapping_fields(record_list)
        data_list = generate_data(record_list)
        request_datareceive(data_list)
    except Exception as e:
        log.error("抽音程序异常")
        log.error(e, exc_info=1)


if __name__ == '__main__':
    # 本地测试时启用
    start_capture()