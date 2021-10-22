# coding=utf-8
import json
import logging
import os
import sys
from math import ceil
sys.path.append('..')
from flask import Flask, request
from MQ.publish_worker_pika import PublishWorker
from config import config

app = Flask(__name__)

# @app.route('/datareceive', methods=['POST'])
# def test():
#     dict = request.get_json()
#     print("param:", dict)
#     return {"result": "sucess"}, 200

# REQUIRED_FIELDS = ['connid', 'calluuid', 'employeeid', 'employeeid_from', 'cde_first_dept_name', ]


@app.route("/record/", methods=["POST"])
def record():
    """
    接收录音随路数据
    """
    log = app.logger
    data_list = request.get_json()
    log.info('接收到请求')
    if not data_list:
        log.error('请求数据非json格式')
        return {'code': 400, 'message': '请发送json格式的请求数据'}
    if len(data_list) == 0:
        log.error('推送数据为空')
        return {'code': 400, 'message': '推送数据为空'}
    log.info(f'数据长度为：{len(data_list)}')
    data_list = lower_key(data_list)

    # 过滤数据
    data_list = filter_data(data_list)
    log.info(f"按规则筛选后的数据量：{len(data_list)}")

    if data_list:
        # 将数据分块发送到队列中
        # TODO 可以按照这种方式 将数据添加到队列中
        publish = PublishWorker(config["QUEUE"])
        for i in range(ceil(len(data_list) / 1000)):
            data_list_sep = data_list[i * 1000:(i + 1) * 1000]
            send_data = {'data_list': data_list_sep}
            publish.send_data_queue(config["QUEUE"]["QUEUE_NAME"], send_data)
            log.info(f'推送 {len(data_list_sep)} 条数据到队列中')

        try:
            # 持久化数据到文件中，补数据用
            data_dict = group_by_date(data_list)
            for date_key in data_dict:
                local_path = create_folder(date_key)
                file_path = write_to_total_records(data_dict[date_key], local_path)
                log.info(f'写入 {len(data_dict[date_key])} 条数据到 {file_path} 文件中')
        except Exception as e:
            log.error("持久化到文件失败")
            log.error(e)

    return {'code': 200, 'message': 'ok'}


def filter_data(data_list):
    """
    按规则过滤数据
    保留坐席部门为 用户服务部 or 工号/呼出工号以 sanyou.cn 结尾 且 通话时长大于0的数据
    """
    new_data_list = []
    for data in data_list:
        if (data.get("cde_first_dept_name") == "用户服务部" or
            (data.get("employeeid", "").endswith("sanyou.cn") or data.get("employeeid_from", "").endswith("sanyou.cn"))) \
                and int(data.get("t_handle", 0)) > 0:
            new_data_list.append(data)
    return new_data_list


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


def write_to_total_records(data_list, local_path):
    """
    将录音数据持久化到文件中 total_records.txt
    :param data_list: 录音数据列表 [{},{}]
    :param local_path: total_records.txt文件所在路径
    """
    file_path = os.path.join(local_path, 'total_records.txt')
    with open(file_path, 'w', encoding='utf-8') as total_records:
        for data in data_list:
            total_records.write(json.dumps(data, ensure_ascii=False) + '\n')
    return file_path


def create_folder(date):
    """
    创建并返回录音文件本地下载目录 DATA_PATH/yyyy-mm-dd
    """
    local_path = os.path.join(config["HTTP"]["DATA_PATH"], date)
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    return local_path


def group_by_date(data_list):
    """
    将数据按日期分组，形成字典：{date: data_list, ...}
    :param data_list:
    :return: 分组后的字典
    """
    data_dict = {}
    for data in data_list:
        date_key = data.get("answer_time")
        if not date_key:
            logging.warning("该条记录无answer_time字段，connid："+data.get("connid"))
            continue
        date_key = date_key[0:10]
        if date_key in data_dict:
            data_dict[date_key].append(data)
        else:
            data_dict[date_key] = [data]
    return data_dict


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
