import json
import os
import sys
import time
from math import ceil

import httpx

# 通过MySQL数据库导入
import pymysql

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
                    log.warning("当前业务含有多个录音文件，connid：" + data.get("connid"))
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
        # 呼叫类型调整
        if data['workflow'] == 'normal':
            data['workflow'] = '呼入'
        elif data['workflow'] == 'dialout':
            data['workflow'] = '呼出'
        # 挂机方向调整
        if data['hanguper'] == 'customer':
            data['hanguper'] = '客户挂机'
        elif data['hanguper'] == 'agent':
            data['hanguper'] = '坐席挂机'


def generate_data(data_list, data_channel):
    """
    生成符合接口规范的数据, 并且子列表每条最大1000条数据
    """
    task_info = []
    for item in data_list:
        data, record_info = {}, {}  # 业务维度, 录音维度
        # TODO 将未序列化的数据页添加到字典
        # record_info = item.copy()
        # 录音字典定制数据
        record_info["record_id"] = item["callId"]  # 通话流水号
        record_info['record_path'] = item['record_path']  # 本地录音地址
        record_info["record_time"] = item["startTime"]  # 录音开始时间
        record_info["record_flag"] = '0'  # 录音状态标记

        if item['workflow'] == '呼入':

            data['customer_phone'] = item['callNo']  # 客户电话
        elif item['workflow'] == '呼出':
            data['customer_phone'] = item['customerPhone']
        else:
            data['customer_phone'] = item['customerPhone']

        data['called_no'] = item['customerPhone']  # 被叫号码
        data['workflow'] = item['workflow']  # 通话流程 in: 呼入
        data['call_result'] = item['callResult']  # 通话结果
        data['agent_id'] = item['agentId']  # 客服ID
        data['agent_name'] = item['agentNickName']  # 客服名称
        data['relevant_agent'] = item['relevantAgent']  # 相关客服
        data['call_no'] = item['callNo']  # 主叫号码
        data['start_time'] = item['startTime']  # 通话开始时间
        data['end_time'] = item['endTime']  # 通话结束时间
        data['supplier_type'] = item['supplierType']  # 供应商类型
        data['call_state'] = item['callState']  # 事件状态
        data['department_name'] = item['departmentName']  # 坐席所属部门
        data['business_type'] = item['business_type']  # 业务类型
        data['hanguper'] = item['hanguper']  # 主叫方

        # 20211109 新增
        data['total_time'] = item['totalTime']  # 通话时长: 秒
        data['drop_side'] = item['dropSide']  # 挂机方向 为空
        data['ring_time'] = item['agentRingAt']  # 来电时间, 响铃时间

        # 构造业务字段
        data["task_id"] = item["callId"]  # TODO 任务流水号 可以自动生成
        data["record_list"] = item["callId"]  # 录音列表
        data["task_time"] = item["startTime"]  # 任务时间
        data["task_flag"] = '0'  # 任务标记 用于后续处理过程状态迁移标记

        # TODO 业务字段 当接口通了或生产环境时需要匹配
        # # 业务字典定制数据
        if len(item['business_data']):
            business_data: dict = item['business_data'][0].copy()  # 获取业务数据中的第一条
            data['order_no'] = business_data['orderNo']  # 订单编号
            data['contract_no'] = business_data['contractNo']  # 合同编号
            data['product_name'] = business_data['productName']  # 产品方案/产品信息
            data['customer_name'] = business_data['customerName']  # 客户姓名
            # data['customer_phone'] = business_data['customerPhoneNo']  # 客户电话
            data['apply_time'] = business_data['applyTime']  # 申请时间
            data['business_type_desc'] = business_data['businessTypeDesc']  # 业务类型 : 信审/客服/催收
            data['marriage_status'] = business_data['marriageStatusDesc']  # 婚姻状况
            data['contact_name_desc'] = business_data['contactNameDesc']  # 联系名称
            data['dealer_no'] = business_data['dealerNo']  # 经销商代码
            data['dealer_name'] = business_data['dealerName']  # 经销商名称
            data['dealer_abbr'] = business_data['dealerAbbreviationName']  # 经销商简称
            data['prequalification_level'] = business_data['preApprovalLevel']  # 预审批等级
            # data['prequalification_level'] = business_data.get('preApprovalLevel', '')  # 预审批等级

            data['credit_review_result'] = business_data['creditReviewResult']  # 信审决策结果
            data['final_approval_result'] = business_data['finalApprovalResult']  # 最终审批结果
            data['handle_time'] = business_data['handleTime']  # 处理时间
            data['application_status'] = business_data['applicationStatusDesc']  # 申请状态描述
            data['customer_problems'] = business_data['customerProblems']  # 客户问题

            # 20211122新增
            data['brand_type'] = business_data['brandType']  # 是否LCV
            data['car_level'] = business_data['carLevel']  # 车辆级别
            data['finance_balance'] = business_data['frze']  # 融资余额
            data['apply_type'] = business_data['applyType']  # 公司性质
            data['bonds_name'] = business_data['bondsName']  # 公户申请人
            data['coll_back_type'] = business_data['collBackType']  # 催收结果
            data['case_end'] = business_data['caseEnd']  # 任务截止日期
            data['node_name'] = business_data['nodeName']  # 审批节点
            data['id_card_no'] = business_data['idCardNo']  # 身份证号
            data['case_date'] = business_data['caseDate']  # 流入日期
            data['contact_name'] = business_data['contactName']  # 流入日期

            # 设置与任务相关的录音信息列表
            data["record_info"] = [record_info]  # 构造录音字段数据
            task_info.append(data)
        else:
            # 该代码默认不会执行
            log.error("未匹配到相关业务接口数据, 将不会推送")

    # 信审类型的task_info 需要重新组装
    if data_channel == 'zyhy_xs':
        task_info1, task_info2 = [], []  # 非重复, 已重复数据
        task_flag_list = []
        new_task_info = []

        # 将元素去重, 重复的添加到新的列表中
        for task in task_info:
            task_flag = (task['order_no'], task['id_card_no'])
            if task_flag not in task_flag_list:
                task_flag_list.append(task_flag)
                task_info1.append(task)
            else:  # 如果已经存在 则将该录音添加到已有的数据上
                task_info2.append(task)

        # 将重复的数据添加到同一个任务中
        for item in task_info1:
            for item2 in task_info2:
                if item['order_no'] == item2['order_no'] and item['id_card_no'] == item2['id_card_no']:
                    item['record_list'] += ',' + item2['record_list']
                    item['record_info'].append(item2['record_info'][0])

            # 将未通过的数据添加到任务中
            with pymysql.connect(host=config['MYSQL']['host'],
                                 port=config['MYSQL']['port'],
                                 user=config['MYSQL']['user'],
                                 passwd=config['MYSQL']['passwd'],
                                 db=config['MYSQL']['db']) as conn:
                with conn.cursor() as cur:
                    cur.execute('select distinct record_id, record_path, record_time, record_flag '
                                'from credit_review '
                                'where id_card_no = %s and order_no = %s', (item['id_card_no'], item['order_no']))
                    for item3 in cur.fetchall():
                        # 将查询到的录音列表数据添加过去
                        item['record_info'].append(dict(record_id=item3[0], record_path=item3[1], record_time=item3[
                            2], record_flag=item3[3]))
                        # 修改录音列表数据 逗号隔开的
                        item['record_list'] += ',' + item3[0]
                        log.info("从数据库中取得未通过数据")

                    # 删除相应不通过数据
                    cur.execute('delete from credit_review where id_card_no = %s and order_no = %s',
                                (item['id_card_no'], item['order_no']))
                conn.commit()
            log.info(f" 订单编号: {item['order_no']}, 身份证号: {item['id_card_no']}, 存在多条录音, 录音列表: {item['record_list']}")

            new_task_info.append(item)

        # 将新的数据赋值给task_info
        task_info = new_task_info
        pass

    log.info(f"已生成 {len(task_info)} 条任务数据")
    # 将task_info数据列表按照 SEND_SIZE 配置项分割成多个部分
    send_size = config["HTTP"]["SEND_SIZE"]
    # 将一个大列表拆分成子列表最多1000个的小列表
    task_info_sep = [task_info[i * send_size:(i + 1) * send_size] for i in
                     range(ceil(len(task_info) / send_size))]
    # 生成接口数据
    # TODO 需要根据 业务类型来判断
    data_tmpl = {
        "data_type": "speech",
        "data_treatment": "batch",
        "data_channel": data_channel,  # TODO zyhy 录音转码命令中需要用到
        "accesskey_id": "asdf",
        "secret": "123456",
        "if_convert": "yes"
    }
    data_list2 = []
    for task_infos in task_info_sep:
        data = data_tmpl.copy()
        data["task_info"] = task_infos
        data_list2.append(data)
    return data_list2, len(task_info)


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
            log.info(f"根据日期: {append_date}手动补数")
            data_list = start_request_data(append_date)  # 请求业务数据
            # data_list = get_data_from_file(append_date, 'total_records.txt')

        if not data_list:
            log.info("无数据需要推送，程序结束...")
            return
        call_record_count = len(data_list)
        log.info(f"共获取通话记录(含录音文件)：{call_record_count}条")

        # TODO 处理失败的数据
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
        mapping_fields(data_list)  # TODO 是否需要映射字段
        # TODO
        data_list1, data_list2, data_list3 = [], [], []

        # 根据业务类型将数据分类
        for data in data_list:
            if data['business_type'] == 'CREDIT_REVIEW':
                data_list1.append(data)
            elif data['business_type'] == 'CUSTOMER_SERVICE':
                data_list2.append(data)
            elif data['business_type'] == 'COLLECTION':
                data_list3.append(data)
            else:
                log.info("未识别的业务类型")

        # TODO 信审类型的数据需要特殊处理并持久化到数据库
        data_list_xs = []
        for xs_data in data_list1:
            if len(xs_data['business_data']) > 0:
                business_data = xs_data['business_data'][0]
                if business_data['finalApprovalResult'] in ('通过', '提首付通过') and business_data['creditReviewResult'] in (
                        '通过',
                        '审批中'):
                    data_list_xs.append(xs_data)
                else:
                    # 信审未通过, 持久化到数据库中
                    with pymysql.connect(host=config['MYSQL']['host'],
                                         port=config['MYSQL']['port'],
                                         user=config['MYSQL']['user'],
                                         passwd=config['MYSQL']['passwd'],
                                         db=config['MYSQL']['db']
                                         ) as conn:
                        with conn.cursor() as cur:
                            cur.execute('insert into credit_review values (default, %s, %s, %s, %s, %s, %s)',
                                        (business_data['orderNo'],
                                         business_data['idCardNo'],
                                         xs_data['callId'],
                                         xs_data['record_path'],
                                         xs_data['startTime'],
                                         '0'))
                            log.info('插入数据库成功')
                        conn.commit()
            else:
                log.info("未匹配到业务数据")  # 一般不会执行, 传入值之前已经过滤
                # 未通过的需要持久化到数据库
                # cur.execute('insert into credit_review values ')

                pass

            pass
        current_date = time.strftime('%Y-%m-%d', time.localtime())
        # 每天尝试删除超过10天且未通过的信审数据
        # TODO 每日删除录音日期超过10天的数据
        with pymysql.connect(host=config['MYSQL']['host'],
                             port=config['MYSQL']['port'],
                             user=config['MYSQL']['user'],
                             passwd=config['MYSQL']['passwd'],
                             db=config['MYSQL']['db']
                             ) as conn:
            with conn.cursor() as cur:
                cur.execute('select version()')
                # cur.execute('delete from credit_review where date(record_time) < date(date_sub(now(),interval 10 day))')
                log.info('删除过期信审数据成功')
            conn.commit()
        # cur.execute(f'delete credit_review where datediff({current_date}, start_time) > 10 ')
        # 获取已通过列表的历史数据

        # log.info(f'将数据推送到抽音框架, 数据列表: 信审-{data_list1}, 客服-{data_list2}, 催收-{data_list3}')
        data_list1, task_info_count1 = generate_data(data_list_xs, 'zyhy_xs')
        data_list2, task_info_count2 = generate_data(data_list2, 'zyhy_kf')
        data_list3, task_info_count3 = generate_data(data_list3, 'zyhy_cs')
        log.info(f"共获取录音文件 {call_record_count}条, 成功匹配业务数据{task_info_count1 + task_info_count2 + task_info_count3}条")
        request_datareceive(data_list1)
        request_datareceive(data_list2)
        request_datareceive(data_list3)
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
        data_list, task_info_count = generate_data(record_list)
        request_datareceive(data_list)
    except Exception as e:
        log.error("抽音程序异常")
        log.error(e, exc_info=1)


if __name__ == '__main__':
    # 本地测试时启用
    start_capture()
