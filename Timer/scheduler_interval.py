# !/usr/bin/env python
# -*- coding=utf-8 -*-

import datetime
import time
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()


@scheduler.scheduled_job("interval", seconds=5, misfire_grace_time=30)
def record_capture_timer():
    print("start current Time", datetime.datetime.now())
    time.sleep(10)
    print("end current Time", datetime.datetime.now())