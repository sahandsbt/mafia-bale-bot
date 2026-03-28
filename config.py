from dotenv import load_dotenv
import logging
import os

# Loading env variables from .env
load_dotenv()

# BOT settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
DATA_DIR = os.path.join(BASE_DIR, 'data')
MEDIA_DIR = os.path.join(DATA_DIR, 'media')

# Creating paths
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Log into console
    ]
)
logger = logging.getLogger(__name__)

# Validating tokens
if not BOT_TOKEN:
    logger.error("FATAL: BOT_TOKEN is available in .env file")
    raise ValueError("BOT_TOKEN is required for the bot to run")

# Export constatns
__all__ = ["BOT_TOKEN", "BASE_DIR", "DATA_DIR", "TMP_DIR", "MEDIA_DIR", "logger"]

logger.info("Configuration finished successfully.")