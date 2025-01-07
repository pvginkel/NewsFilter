from .app import App
import logging

logging.basicConfig(
    format="%(relativeCreated)s - [%(levelname)s] %(message)s (%(name)s)",
    level=logging.INFO,
)


def main():
    App().run()
