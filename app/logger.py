import logging
import sys


def setup_logging(level=logging.INFO):
    """Configure logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create a formatter with timestamp, level, and message
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H-%M-%S",
    )

    # Create console handler and attach formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_logger(name):
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
