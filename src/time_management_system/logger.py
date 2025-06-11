"""Universal logger setup for the entire repository."""

import logging
import sys

APP_NAME = "TMS"

# Configure logging only once, when this module is imported
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

root_logger = logging.getLogger()
if not root_logger.hasHandlers():
    root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)


# Helper function for modules to get their own static logger
def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for the specified module name, namespaced under the app name."""
    return logging.getLogger(f"{APP_NAME}.{module_name}")
