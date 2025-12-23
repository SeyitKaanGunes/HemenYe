# app/logging_config.py - application logging setup
import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    if app.testing or app.debug:
        return
    log_dir = os.path.abspath(os.path.join(app.root_path, "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "hemenye.log")

    if any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        return

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
