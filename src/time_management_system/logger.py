import logging
from pathlib import Path
import sys

# Universal logger setup for the entire repository
APP_NAME = "TMS"
MODULE_NAME = Path(__file__).stem

logger = logging.getLogger(f"{APP_NAME}.{MODULE_NAME}")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(handler)
