import logging
import sys

from args import Config
from server import Server


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    config = Config()
    server = Server(port=config.port, origin=config.origin)

    if config.clear_cache:
        server.clear_cache()
        print("Cache cleared.")
        sys.exit(0)

    server.start()


if __name__ == "__main__":
    main()
