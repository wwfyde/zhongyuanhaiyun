import json
import os
import sys
from math import ceil

# 通过MySQL数据库导入
from DB.mysql_base import MysqlBase
from MQ.publish_worker_pika import PublishWorker
from config import config
from HTTP.RecordDataRequests import request_datareceive
from log import record_log as log


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


def generate_data(data_list):
    """
    生成符合接口规范的数据
    """
    task_info = []
    for data in data_list:
        record_info = data.copy()
        # 指定record_id
        record_info["record_id"] = record_info["calluuid"]
        # 指定record_time
        record_info["record_time"] = record_info["answer_time"]
        # 设置record_flag固定值0
        record_info["record_flag"] = '0'
        # 指定task_id
        data["task_id"] = data["connid"]
        # 指定录音列表id
        data["record_list"] = data["calluuid"]
        # 指定任务时间
        data["task_time"] = data["answer_time"]
        # 设置task_flag固定值0
        data["task_flag"] = '0'
        # 设置与任务相关的录音信息列表
        data["record_info"] = [record_info]
        task_info.append(data)
    log.info(f"已生成 {len(task_info)} 条任务数据")
    # 将task_info数据列表按照 SEND_SIZE 配置项分割成多个部分
    send_size = config["HTTP"]["SEND_SIZE"]
    task_info_sep = [task_info[i * send_size:(i + 1) * send_size] for i in
                     range(ceil(len(task_info) / send_size))]
    # 生成接口数据
    data_tmpl = {
        "data_type": "speech",
        "data_treatment": "batch",
        "data_channel": "tuhu",
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
            data_list = get_data_from_queue()
        else:
            # 手动补数
            data_list = get_data_from_file(append_date, 'total_records.txt')
        if not data_list:
            log.info("无数据需要推送，程序结束...")
            return
        log.info(f"获取数据量：{len(data_list)}")
        record_list, failed_data_list = parse_path(data_list)
        log.info(f"滤除空路径后的数据量：{len(record_list)}")
        log.info(f"无对应录音文件的数据量：{len(failed_data_list)}")
        if failed_data_list:
            local_path = os.path.join(config["HTTP"]["DATA_PATH"], failed_data_list[0]["answer_time"][:10])
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            file_path = write_to_failed_records(failed_data_list, local_path)
            log.info(f'写入 {len(failed_data_list)} 条数据到 {file_path} 文件中')
        if not record_list:
            log.info("不存在有录音文件的数据，程序结束...")
            return
        mapping_fields(record_list)
        data_list = generate_data(record_list)
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
