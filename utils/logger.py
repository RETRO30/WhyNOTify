import sys
from loguru import logger
import os
from datetime import datetime
from utils.config import Config


def logging_setup():
    format_info = "<green>{time:HH:mm:ss}</green> | <blue>{level}</blue> | <level>{message}</level>"
    logger.remove()

    if not os.path.exists("./logs/"):
        os.mkdir("./logs/")

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"./logs/log_{current_time}.log"
    logger.add(log_filename, format=format_info, level=Config.logger.level)

    logger.add(sys.stdout, colorize=True, format=format_info, level=Config.logger.level)


logging_setup()