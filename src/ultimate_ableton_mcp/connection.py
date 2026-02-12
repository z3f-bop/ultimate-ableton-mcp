"""TCP connection manager for Ableton Live Remote Script communication."""

import json
import logging
import os
import socket
import time
import uuid

logger = logging.getLogger("ultimate-ableton-mcp")

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9877
RECV_BUFFER = 65536
CONNECT_TIMEOUT = 5.0
COMMAND_TIMEOUT = 15.0


class AbletonConnection:
    """Manages TCP connection to the Ableton Remote Script.

    Uses newline-delimited JSON protocol with request IDs for
    concurrent request support.
    """

    def __init__(self):
        self.host = os.environ.get("ABLETON_MCP_HOST", DEFAULT_HOST)
        self.port = int(os.environ.get("ABLETON_MCP_PORT", DEFAULT_PORT))
        self._sock: socket.socket | None = None

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def connect(self) -> None:
        if self._sock:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT)
            sock.connect((self.host, self.port))
            sock.settimeout(None)
            self._sock = sock
            logger.info("Connected to Ableton at %s:%d", self.host, self.port)
        except Exception as e:
            logger.error("Failed to connect to Ableton: %s", e)
            raise ConnectionError(
                f"Cannot connect to Ableton at {self.host}:{self.port}. "
                "Is the Remote Script loaded?"
            ) from e

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
            logger.info("Disconnected from Ableton")

    def send(self, action: str, params: dict | None = None) -> dict:
        """Send a command and wait for the matching response.

        Returns the result dict on success, raises on error.
        """
        if not self._sock:
            self.connect()

        request_id = f"req_{uuid.uuid4().hex[:8]}"
        command = {"id": request_id, "action": action, "params": params or {}}
        payload = json.dumps(command) + "\n"

        try:
            self._sock.sendall(payload.encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            self._sock = None
            raise ConnectionError(f"Lost connection to Ableton: {e}") from e

        # Read response lines until we find ours
        response = self._read_response(request_id)

        if not response.get("ok", False):
            error = response.get("error", "Unknown error from Ableton")
            code = response.get("code", "UNKNOWN")
            raise RuntimeError(f"[{code}] {error}")

        return response.get("result", {})

    def _read_response(self, request_id: str) -> dict:
        """Read newline-delimited JSON until we find our request_id."""
        buffer = ""
        self._sock.settimeout(COMMAND_TIMEOUT)

        try:
            while True:
                chunk = self._sock.recv(RECV_BUFFER)
                if not chunk:
                    self._sock = None
                    raise ConnectionError("Ableton closed the connection")

                buffer += chunk.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from Ableton: %s", line[:200])
                        continue

                    if msg.get("id") == request_id:
                        return msg
                    # Not our response — discard (or could queue for other consumers)
                    logger.debug("Discarding response for %s", msg.get("id"))
        except socket.timeout:
            raise TimeoutError(
                f"Timeout waiting for response to {request_id}"
            )
        finally:
            if self._sock:
                self._sock.settimeout(None)


# Module-level singleton
_connection: AbletonConnection | None = None


def get_connection() -> AbletonConnection:
    """Get or create the singleton connection."""
    global _connection
    if _connection is None:
        _connection = AbletonConnection()
    if not _connection.connected:
        _connection.connect()
    return _connection


def shutdown_connection() -> None:
    """Cleanly close the connection."""
    global _connection
    if _connection:
        _connection.disconnect()
        _connection = None
