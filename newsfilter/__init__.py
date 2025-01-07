import logging

__version__ = "0.1.0"

logging.basicConfig(
    format="%(relativeCreated)s - [%(levelname)s] %(message)s (%(name)s)",
    level=logging.INFO,
)
