# dynamic_main/logger_setup.py


from log.logger import logger
from Config.AppConfig.config import LOG_DIR, LOG_FILE, LOGGING_LEVEL

import os
import logging


def setup_logger():
    log_path = os.path.join(os.path.dirname(__file__), '..', '..', LOG_DIR, LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Konfigurera loggern
    logger.setLevel(LOGGING_LEVEL)

    # Skapa filhanterare
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(LOGGING_LEVEL)

    # Skapa formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Lägg till handler till loggern
    logger.addHandler(file_handler)

    # Eventuellt lägga till andra handlers, t.ex., stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.debug("Logger setup completed.")

# def setup_logger():
#     logger.setLevel("DEBUG")  # Adjust to the appropriate method for setting log level
