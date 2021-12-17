import datetime
import os
import shutil
from apscheduler.schedulers.blocking import BlockingScheduler
from record_capture import start_capture, append_failed
from HTTP.record_data_httpx import start_request_data
from config import config

scheduler = BlockingScheduler()


# # TODO 定时读取第三方接口并添加到队列
# @scheduler.scheduled_job("cron", second=config["TIMER"]["CAPTURE_SEC"], minute=config["TIMER"]["CAPTURE_MIN"],
#                          hour=config["TIMER"]["CAPTURE_HOUR"], misfire_grace_time=30, max_instances=10)
# def get_record_data():
#     """
#     数据获取定时任务, 定时从第三方数据请求数据并推送到抽音框架
#
#     每天凌晨一点获取前一日数据
#     :return:
#     """
#     # start_request_data()
#     pass

@scheduler.scheduled_job("cron", second=config["TIMER"]["CAPTURE_SEC"], minute=config["TIMER"]["CAPTURE_MIN"],
                         hour=config["TIMER"]["CAPTURE_HOUR"], misfire_grace_time=30, max_instances=10)
def record_capture_timer():
    """
    录音抽音定时任务
    """
    start_capture()


@scheduler.scheduled_job("cron", second=config["TIMER"]["FAILED_SEC"], minute=config["TIMER"]["FAILED_MIN"],
                         hour=config["TIMER"]["FAILED_HOUR"], misfire_grace_time=30, max_instances=10)
def record_append_timer():
    """
    重推失败数据定时任务
    """
    date = (datetime.date.today() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
    append_failed(date)

@scheduler.scheduled_job("cron", second=config["TIMER"]["CLEAR_SEC"], minute=config["TIMER"]["CLEAR_MIN"],
                         hour=config["TIMER"]["CLEAR_HOUR"], misfire_grace_time=30, max_instances=10)
def clear_timer():
    """
    清理原始录音文件定时任务
    """
    RECORD_STORAGE_DAYS = config["TIMER"]["RECORD_STORAGE_DAYS"]  # 录音存储天数
    # log.info(f"清理超 {RECORD_STORAGE_DAYS} 天的录音文件...")
    earliest_day = (datetime.date.today() + datetime.timedelta(days=-RECORD_STORAGE_DAYS)).strftime('%Y-%m-%d')
    for dir_name in os.listdir(config["HTTP"]["RECORD_PATH"]):
        if dir_name < earliest_day:
            # log.info(f"清理录音文件夹：{config['HTTP']['RECORD_PATH']}/{dir_name}")
            shutil.rmtree(os.path.join(config['HTTP']['RECORD_PATH'], dir_name))
