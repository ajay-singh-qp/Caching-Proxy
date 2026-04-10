import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import httpx

logger = logging.getLogger(__name__)

type _CacheEntry = tuple[int, dict[str, str], bytes]


class ProxyHandler(BaseHTTPRequestHandler):
    """Per-request handler that serves cached or freshly fetched responses."""

    origin: ClassVar[str] = ""
    _client: ClassVar[httpx.Client]
    _cache: ClassVar[dict[str, _CacheEntry]] = {}

    def do_GET(self) -> None:
        if (entry := self._cache.get(self.path)) is not None:
            status, headers, body = entry
            self._respond(status, {**headers, "X-Cache": "HIT"}, body)
            return

        try:
            upstream = self._client.get(f"{self.origin}{self.path}")
        except httpx.RequestError as exc:
            logger.error("Upstream request failed for %s: %s", self.path, exc)
            self.send_error(502, "Bad Gateway")
            return

        headers: dict[str, str] = {"X-Cache": "MISS"}
        if ct := upstream.headers.get("content-type"):
            headers["Content-Type"] = ct

        self._cache[self.path] = (upstream.status_code, headers, upstream.content)
        self._respond(upstream.status_code, headers, upstream.content)

    def _respond(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        logger.debug(fmt, *args)


class Server:
    def __init__(self, port: int, origin: str) -> None:
        ProxyHandler.origin = origin
        ProxyHandler._client = httpx.Client(follow_redirects=True)
        self._httpd = HTTPServer(("localhost", port), ProxyHandler)

    def clear_cache(self) -> None:
        ProxyHandler._cache.clear()

    def start(self) -> None:
        host, port = self._httpd.server_address
        logger.info("Proxy listening on http://%s:%d -> %s", host, port, ProxyHandler.origin)
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down.")
        finally:
            ProxyHandler._client.close()
            self._httpd.server_close()
