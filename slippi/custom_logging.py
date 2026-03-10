import logging
import sys


_FORMAT_STRING = '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'


def init():
  logger = logging.getLogger('slippy-api')
  logger.setLevel(logging.DEBUG)

  stdout_handler = logging.StreamHandler(sys.stdout)
  file_handler = logging.FileHandler('log.log')

  stdout_handler.setLevel(logging.DEBUG)
  file_handler.setLevel(logging.DEBUG)

  formatter = logging.Formatter(_FORMAT_STRING)
  stdout_handler.setFormatter(CustomFormatter())
  file_handler.setFormatter(formatter)

  logger.addHandler(stdout_handler)
  logger.addHandler(file_handler)


class CustomFormatter(logging.Formatter):

  grey = "\x1b[38;20m"
  yellow = "\x1b[33;20m"
  red = "\x1b[31;20m"
  bold_red = "\x1b[31;1m"
  reset = "\x1b[0m"

  FORMATS = {
    logging.DEBUG: grey + _FORMAT_STRING + reset,
    logging.INFO: grey + _FORMAT_STRING + reset,
    logging.WARNING: yellow + _FORMAT_STRING + reset,
    logging.ERROR: red + _FORMAT_STRING + reset,
    logging.CRITICAL: bold_red + _FORMAT_STRING + reset,
  }

  def get_logger(self) -> logging.Logger:
    return logging.getLogger('slippy-api')

  def format(self, record: logging.LogRecord) -> str:
    log_fmt = self.FORMATS.get(record.levelno)
    return logging.Formatter(log_fmt).format(record)


init()
