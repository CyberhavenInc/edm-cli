import logging
from .command_dispatcher import CommandDispatcher

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO, force=True)


def main():
    dispatcher = CommandDispatcher()
    dispatcher.capture()


if __name__ == "__main__":
    main()
