import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import LOG_PATH
from app.config import debug


def init_logger():
    logger = logging.getLogger("GFSSrefund")

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    Path(LOG_PATH).mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    )

    # console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # файл с ротацией
    file_handler = RotatingFileHandler(
        f"{LOG_PATH}/refund.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info("Логирование приложения запущено")

    return logger


log = init_logger()