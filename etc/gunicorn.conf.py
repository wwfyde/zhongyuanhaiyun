# gunicorn.conf

# 并行工作进程数
workers = 4
# 指定每个工作者的线程数
threads = 2
# 监听内网端口
bind = '0.0.0.0:9090'
# 设置守护进程
daemon = 'true'
# 工作模式协程
worker_class = 'gevent'
# 设置最大并发量
worker_connections = 100
# 设置进程文件目录
pidfile = 'gunicorn.pid'
# 设置访问日志和错误信息日志路径
accesslog = 'log/gunicorn-access.log'
errorlog = 'log/gunicorn-error.log'
# 设置日志记录水平
loglevel = 'info'