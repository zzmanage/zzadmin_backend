# Gunicorn配置文件 - 用于生产环境

# 绑定地址和端口
bind = "127.0.0.1:8000"

# 工作进程数量
# 推荐值: 2 * CPU核心数 + 1
workers = 3

# 工作进程类型
worker_class = "sync"

# 最大请求数 - 超过后自动重启工作进程
max_requests = 1000
max_requests_jitter = 50

# 日志设置
accesslog = "-"  # 输出到标准输出
errorlog = "-"  # 输出到标准错误
loglevel = "info"

# 每个工作进程的最大并发连接数
bind_workers = 1000

# 超时设置
timeout = 30
keepalive = 2

# 进程名称
app_name = "backend_management"
proc_name = "%(app_name)s"

# 环境变量 - 这些会被.env文件中的配置覆盖
# 但为了确保关键环境变量被设置，这里可以再次声明
env = [
    "DJANGO_SETTINGS_MODULE=backend_management.settings",
]

# 其他优化设置
django_settings = "backend_management.settings"
