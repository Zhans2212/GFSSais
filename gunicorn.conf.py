bind = "127.0.0.1:5200"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
forwarded_allow_ips = "*"
wsgi_app="app.main:app"

reload=False

# Таймауты
timeout = 60
graceful_timeout = 30
keepalive = 5


# Логи
loglevel = 'info'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
accesslog = "logs/refund-gunicorn-access.log"
error_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s"  "%(a)s"'
errorlog = "logs/refund-gunicorn-error.log"


# Ограничение запросов (защита от DoS)
max_requests = 2000
max_requests_jitter = 200
