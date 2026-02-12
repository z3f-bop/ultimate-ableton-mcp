"""Shared fixtures and mock infrastructure for testing."""

import json
import socket
import threading
import time

import pytest

from mocks import (  # noqa: F401 — re-exported for test modules
    MockParam, MockMixerDevice, MockDevice, MockClip, MockEnvelope,
    MockClipSlot, MockRoutingType, MockTrack, MockScene, MockGroovePool,
    MockView, MockSong, MockBrowserItem, MockBrowser, MockApplication,
    MockCInstance,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_song():
    """A fresh MockSong for handler tests."""
    return MockSong()


@pytest.fixture
def mock_c_instance(mock_song):
    """A fresh MockCInstance with the mock song."""
    return MockCInstance(mock_song)


# ---------------------------------------------------------------------------
# TCP echo server for connection tests
# ---------------------------------------------------------------------------

class FakeAbletonServer:
    """A TCP server that simulates the Remote Script's wire protocol.

    Receives newline-delimited JSON, responds with matching request IDs.
    """

    def __init__(self, host="localhost", port=0):
        self.host = host
        self.port = port  # 0 = OS picks an available port
        self._server_socket = None
        self._thread = None
        self._running = False
        self._handler = None  # callable(request_dict) -> result_dict

    @property
    def actual_port(self):
        if self._server_socket:
            return self._server_socket.getsockname()[1]
        return self.port

    def start(self, handler=None):
        """Start the server. handler(request) -> result dict."""
        self._handler = handler or (lambda req: {"echo": req["action"]})
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(1)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # Wait for server to be ready
        time.sleep(0.05)

    def stop(self):
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self):
        self._server_socket.settimeout(0.5)
        while self._running:
            try:
                client, _ = self._server_socket.accept()
                t = threading.Thread(target=self._handle_client,
                                     args=(client,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client):
        buffer = ""
        client.settimeout(5.0)
        try:
            while self._running:
                try:
                    data = client.recv(65536)
                except socket.timeout:
                    continue
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        request = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    request_id = request.get("id", "unknown")
                    try:
                        result = self._handler(request)
                        response = {"id": request_id, "ok": True, "result": result}
                    except Exception as e:
                        response = {"id": request_id, "ok": False,
                                    "error": str(e), "code": "HANDLER_ERROR"}

                    resp_line = json.dumps(response) + "\n"
                    client.sendall(resp_line.encode("utf-8"))
        except Exception:
            pass
        finally:
            try:
                client.close()
            except Exception:
                pass


@pytest.fixture
def fake_server():
    """A FakeAbletonServer that starts/stops around the test."""
    server = FakeAbletonServer()
    yield server
    server.stop()
