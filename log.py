import logging
import os
from logging.handlers import TimedRotatingFileHandler

from config import config

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)
fmt = logging.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s"
    )
sh = logging.StreamHandler()
sh.setFormatter(fmt)
root_log.addHandler(sh)


def get_log(log_name):
    log = logging.getLogger(log_name)
    log.propagate = 0
    log.setLevel(logging.INFO)
    log_path = config['LOG']['LOG_PATH']
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_file = os.path.join(log_path, log_name+'-datacapture.log')
    fh = TimedRotatingFileHandler(filename=log_file, when="midnight", backupCount=30)
    fh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)
    return log


record_log = get_log('record')
text_log = get_log('text')
# logging.getLogger('apscheduler.scheduler').propagate=1