import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "bot.log"


def configure_logging() -> None:
  if logging.getLogger().handlers:
    return

  _LOG_DIR.mkdir(parents=True, exist_ok=True)

  formatter = logging.Formatter(_LOG_FORMAT)

  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)

  file_handler = RotatingFileHandler(_LOG_FILE, maxBytes=2_000_000, backupCount=3)
  file_handler.setFormatter(formatter)

  logging.basicConfig(level=logging.INFO, handlers=[stream_handler, file_handler])


def get_logger(name: str) -> logging.Logger:
  configure_logging()
  return logging.getLogger(name)
