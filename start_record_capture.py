import re
import sys

from record_capture import start_capture


if __name__ == '__main__':
    cmd = sys.argv[1:2][0] if sys.argv[1:2] else ""
    if cmd == "start":
        from Timer.scheduler_cron import scheduler
        # 程序入口 调度定时任务, 定时开始请求第三方接口
        scheduler.start()
    elif cmd == "append":
        date = str(sys.argv[2:3][0])
        if not re.fullmatch(r'^\d{4}-\d{2}-\d{2}$', date):
            print('日期错误，格式：yyyy-mm-dd')
            sys.exit()
        start_capture(date)
    else:
        print('指令错误')
