import argparse


class Config:
    """Singleton that parses and exposes CLI arguments exactly once."""

    _instance: "Config | None" = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._parse()
        return cls._instance

    def _parse(self) -> None:
        parser = argparse.ArgumentParser(
            description="HTTP caching proxy",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("--port", type=int, required=True, help="Local port to listen on")
        parser.add_argument(
            "--origin",
            type=str,
            required=True,
            help="Origin server URL (e.g. http://example.com)",
        )
        parser.add_argument("--clear-cache", action="store_true", help="Clear the cache and exit")
        self._args = parser.parse_args()

    @property
    def port(self) -> int:
        return self._args.port

    @property
    def origin(self) -> str:
        return self._args.origin.rstrip("/")

    @property
    def clear_cache(self) -> bool:
        return self._args.clear_cache
