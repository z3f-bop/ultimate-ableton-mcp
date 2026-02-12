"""Tests for the TCP connection manager."""

import json
import os
import socket
import threading
import time
from unittest.mock import patch

import pytest

from ultimate_ableton_mcp.connection import (
    AbletonConnection,
    DEFAULT_HOST,
    DEFAULT_PORT,
    get_connection,
    shutdown_connection,
)


class TestAbletonConnectionInit:
    """Test connection initialization and configuration."""

    def test_defaults(self):
        conn = AbletonConnection()
        assert conn.host == DEFAULT_HOST
        assert conn.port == DEFAULT_PORT
        assert conn.connected is False

    def test_env_override_host(self, monkeypatch):
        monkeypatch.setenv("ABLETON_MCP_HOST", "192.168.1.50")
        conn = AbletonConnection()
        assert conn.host == "192.168.1.50"

    def test_env_override_port(self, monkeypatch):
        monkeypatch.setenv("ABLETON_MCP_PORT", "12345")
        conn = AbletonConnection()
        assert conn.port == 12345

    def test_env_invalid_port_raises(self, monkeypatch):
        monkeypatch.setenv("ABLETON_MCP_PORT", "not_a_number")
        with pytest.raises(ValueError):
            AbletonConnection()


class TestAbletonConnectionConnect:
    """Test connect/disconnect lifecycle."""

    def test_connect_to_running_server(self, fake_server):
        fake_server.start()
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        conn.connect()
        assert conn.connected is True
        conn.disconnect()
        assert conn.connected is False

    def test_connect_no_server_raises(self):
        conn = AbletonConnection()
        conn.host = "localhost"
        conn.port = 1  # almost certainly nothing running here
        with pytest.raises(ConnectionError, match="Cannot connect"):
            conn.connect()

    def test_double_connect_is_noop(self, fake_server):
        fake_server.start()
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        conn.connect()
        sock_id = id(conn._sock)
        conn.connect()  # should not create new socket
        assert id(conn._sock) == sock_id
        conn.disconnect()

    def test_disconnect_when_not_connected_is_safe(self):
        conn = AbletonConnection()
        conn.disconnect()  # should not raise


class TestAbletonConnectionSend:
    """Test the send/receive protocol."""

    def test_send_receives_matching_response(self, fake_server):
        fake_server.start(handler=lambda req: {"tempo": 140.0})
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        result = conn.send("set_tempo", {"bpm": 140})
        assert result == {"tempo": 140.0}
        conn.disconnect()

    def test_send_auto_connects(self, fake_server):
        fake_server.start(handler=lambda req: {"connected": True})
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        assert conn.connected is False
        result = conn.send("ping")
        assert result == {"connected": True}
        assert conn.connected is True
        conn.disconnect()

    def test_send_error_response_raises_runtime_error(self, fake_server):
        def error_handler(req):
            raise ValueError("BPM out of range")

        fake_server.start(handler=error_handler)
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        with pytest.raises(RuntimeError, match="BPM out of range"):
            conn.send("set_tempo", {"bpm": -5})
        conn.disconnect()

    def test_send_includes_request_id(self, fake_server):
        captured = {}

        def capture_handler(req):
            captured.update(req)
            return {"ok": True}

        fake_server.start(handler=capture_handler)
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        conn.send("test_action", {"key": "val"})
        assert "id" in captured
        assert captured["id"].startswith("req_")
        assert captured["action"] == "test_action"
        assert captured["params"] == {"key": "val"}
        conn.disconnect()

    def test_send_with_no_params(self, fake_server):
        captured = {}

        def capture_handler(req):
            captured.update(req)
            return {}

        fake_server.start(handler=capture_handler)
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        conn.send("undo")
        assert captured["params"] == {}
        conn.disconnect()

    def test_multiple_sequential_commands(self, fake_server):
        call_count = {"n": 0}

        def counting_handler(req):
            call_count["n"] += 1
            return {"call": call_count["n"]}

        fake_server.start(handler=counting_handler)
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        r1 = conn.send("cmd1")
        r2 = conn.send("cmd2")
        r3 = conn.send("cmd3")
        assert r1["call"] == 1
        assert r2["call"] == 2
        assert r3["call"] == 3
        conn.disconnect()


class TestAbletonConnectionEdgeCases:
    """Test error conditions and edge cases."""

    def test_server_closes_connection_mid_send(self, fake_server):
        """If the server closes the socket, send should raise ConnectionError."""
        fake_server.start()
        conn = AbletonConnection()
        conn.host = fake_server.host
        conn.port = fake_server.actual_port
        conn.connect()

        # Forcibly close the underlying socket to simulate broken pipe
        conn._sock.close()

        with pytest.raises((ConnectionError, RuntimeError, OSError)):
            conn.send("after_close")

    def test_newline_delimited_protocol(self, fake_server):
        """Verify we send newline-terminated JSON."""
        received_raw = {"data": b""}

        original_start = fake_server.start

        # We need a raw-level check, so we'll use a real socket pair
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("localhost", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        def accept_and_echo():
            server_sock.settimeout(5.0)
            client, _ = server_sock.accept()
            data = client.recv(65536)
            received_raw["data"] = data
            # Parse and echo back
            line = data.decode("utf-8").strip()
            req = json.loads(line)
            resp = json.dumps({"id": req["id"], "ok": True, "result": {}}) + "\n"
            client.sendall(resp.encode("utf-8"))
            client.close()
            server_sock.close()

        t = threading.Thread(target=accept_and_echo, daemon=True)
        t.start()

        conn = AbletonConnection()
        conn.host = "localhost"
        conn.port = port
        conn.send("test")
        t.join(timeout=2.0)

        raw = received_raw["data"].decode("utf-8")
        assert raw.endswith("\n"), "Payload must be newline-terminated"
        parsed = json.loads(raw.strip())
        assert "id" in parsed
        assert parsed["action"] == "test"
        conn.disconnect()


class TestSingletonConnection:
    """Test the module-level get_connection/shutdown_connection."""

    def test_get_connection_returns_same_instance(self, fake_server):
        fake_server.start()

        with patch.dict(os.environ, {"ABLETON_MCP_PORT": str(fake_server.actual_port)}):
            shutdown_connection()  # clean state
            c1 = get_connection()
            c2 = get_connection()
            assert c1 is c2
            shutdown_connection()

    def test_shutdown_cleans_up(self, fake_server):
        fake_server.start()

        with patch.dict(os.environ, {"ABLETON_MCP_PORT": str(fake_server.actual_port)}):
            shutdown_connection()  # clean state
            c1 = get_connection()
            assert c1.connected
            shutdown_connection()
            # After shutdown, get_connection should create a new instance
            c2 = get_connection()
            assert c2 is not c1
            shutdown_connection()
