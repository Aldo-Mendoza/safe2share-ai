# FILE: src/safe2share/logconfig.py

import logging
import sys
from .config import settings

APP_LOGGER_NAME = "safe2share"

logger = logging.getLogger(APP_LOGGER_NAME) 


def setup_logging():
    """Configures the root logging handler based on settings."""
    
    if logger.handlers:
        return

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.setLevel(level)


setup_logging()