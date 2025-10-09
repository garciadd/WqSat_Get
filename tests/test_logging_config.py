import os
import logging

import pytest

from wqsat_get import logging_config
from wqsat_get import utils


def test_setup_logging_creates_logfile(monkeypatch, tmp_path):
    """
    setup_logging should create a 'logs' directory and a log file with timestamped name.
    """
    # redirect base_dir to temporary directory
    monkeypatch.setattr(utils, 'base_dir', lambda: tmp_path)
    # call setup_logging
    logging_config.setup_logging()
    logs_dir = tmp_path / 'logs'
    assert logs_dir.exists() and logs_dir.is_dir()
    # there should be at least one log file in logs
    files = list(logs_dir.iterdir())
    assert files
    # file name should start with 'wqsat_get_' and end with '.log'
    assert any(f.name.startswith('wqsat_get_') and f.name.endswith('.log') for f in files)

    # ensure root logger has two handlers (file and console)
    logger = logging.getLogger()
    handlers = logger.handlers
    assert len(handlers) >= 2
    # file handler should be set to DEBUG and console to INFO
    levels = sorted(h.level for h in handlers)
    assert logging.DEBUG in levels and logging.INFO in levels