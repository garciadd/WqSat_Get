import logging
from datetime import datetime

from . import utils

def setup_logging():
    # Logs path
    root_path = utils.base_dir()
    logs_dir = root_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_filename = logs_dir / f"wqsat_get_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Log format
    log_format = "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    # Save ALL (DEBUG+)
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console Handler: INFO+ only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_filename}")