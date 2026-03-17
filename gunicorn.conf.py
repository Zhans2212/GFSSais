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
loglevel = "info"
accesslog = "-"
errorlog = "-"


# Ограничение запросов (защита от DoS)
max_requests = 2000
max_requests_jitter = 200
