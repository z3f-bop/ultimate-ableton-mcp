"""Tests for the Remote Script core — dispatch table, queue architecture,
and end-to-end socket protocol."""

import json
import queue
import socket
import threading
import time
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "remote_script"))

from mocks import MockSong, MockCInstance
from UltimateAbletonMCP import UltimateAbletonMCP, create_instance


# We need to patch socket binding for tests
@pytest.fixture
def mock_c_instance_for_script(mock_song, mock_c_instance, monkeypatch):
    """Prevent the constructor from binding a real socket."""
    monkeypatch.setattr("UltimateAbletonMCP.socket.socket", lambda *a, **kw: _FakeSocket())
    return mock_c_instance


class _FakeSocket:
    """Minimal socket mock to prevent actual TCP binding in constructor."""

    def setsockopt(self, *a):
        pass

    def bind(self, *a):
        pass

    def listen(self, *a):
        pass

    def settimeout(self, *a):
        pass

    def accept(self):
        raise socket.timeout()

    def close(self):
        pass

    def getsockname(self):
        return ("localhost", 9877)


class TestCreateInstance:
    def test_create_instance(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        assert isinstance(instance, UltimateAbletonMCP)
        instance.disconnect()


class TestDispatchTable:
    """Verify the dispatch table covers all expected actions."""

    def test_dispatch_table_built(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        dispatch = instance._dispatch

        # Spot-check key actions from each handler
        assert "get_session_state" in dispatch
        assert "start_playback" in dispatch
        assert "list_tracks" in dispatch
        assert "create_clip" in dispatch
        assert "list_devices" in dispatch
        assert "list_scenes" in dispatch
        assert "get_browser_tree" in dispatch

        instance.disconnect()

    def test_all_dispatch_values_are_callable(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        for action, method in instance._dispatch.items():
            assert callable(method), f"{action} is not callable"
        instance.disconnect()

    def test_no_duplicate_actions_across_handlers(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        # Count total actions from individual handlers
        total_from_handlers = 0
        for handler in instance._handlers.values():
            total_from_handlers += len(handler.get_actions())

        # Should match dispatch table size (no collisions)
        assert len(instance._dispatch) == total_from_handlers
        instance.disconnect()


class TestExecute:
    """Test the _execute dispatch method."""

    def test_valid_action(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        response = instance._execute("get_session_state", {})
        assert response["ok"] is True
        assert "result" in response
        assert response["result"]["tempo"] == 120.0
        instance.disconnect()

    def test_unknown_action(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        response = instance._execute("nonexistent_action", {})
        assert response["ok"] is False
        assert response["code"] == "UNKNOWN_ACTION"
        instance.disconnect()

    def test_handler_error(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)
        # This should raise because track_index 99 is out of range
        response = instance._execute("get_track", {"track_index": 99})
        assert response["ok"] is False
        assert response["code"] == "EXECUTION_ERROR"
        instance.disconnect()


class TestUpdateDisplay:
    """Test the main-thread queue drain."""

    def test_drains_command_queue(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)

        # Simulate a command being enqueued
        rq = queue.Queue()
        with instance._response_lock:
            instance._response_queues["test_001"] = rq

        instance._command_queue.put(("test_001", "get_session_state", {}))

        # Simulate Live calling update_display
        instance.update_display()

        # Response should be in the response queue
        assert not rq.empty()
        response = rq.get_nowait()
        assert response["id"] == "test_001"
        assert response["ok"] is True
        instance.disconnect()

    def test_multiple_commands_processed(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)

        responses = {}
        for i in range(5):
            req_id = "multi_%d" % i
            rq = queue.Queue()
            with instance._response_lock:
                instance._response_queues[req_id] = rq
            instance._command_queue.put((req_id, "get_session_state", {}))
            responses[req_id] = rq

        instance.update_display()

        for req_id, rq in responses.items():
            assert not rq.empty(), f"No response for {req_id}"
            r = rq.get_nowait()
            assert r["ok"] is True
        instance.disconnect()

    def test_error_in_one_doesnt_block_others(self, mock_c_instance_for_script):
        instance = create_instance(mock_c_instance_for_script)

        rq_good = queue.Queue()
        rq_bad = queue.Queue()

        with instance._response_lock:
            instance._response_queues["good"] = rq_good
            instance._response_queues["bad"] = rq_bad

        instance._command_queue.put(("bad", "nonexistent", {}))
        instance._command_queue.put(("good", "get_session_state", {}))

        instance.update_display()

        bad_resp = rq_bad.get_nowait()
        assert bad_resp["ok"] is False

        good_resp = rq_good.get_nowait()
        assert good_resp["ok"] is True
        instance.disconnect()


class TestEndToEndProtocol:
    """Integration test: real TCP socket communication with the Remote Script."""

    @pytest.fixture
    def live_instance(self, mock_song, mock_c_instance):
        """Create a real Remote Script instance with actual TCP socket."""
        # Use a random available port
        os.environ["ABLETON_MCP_PORT"] = "0"
        instance = UltimateAbletonMCP(mock_c_instance)
        # Get the actual port
        port = instance._server_socket.getsockname()[1]
        yield instance, port
        instance.disconnect()
        os.environ.pop("ABLETON_MCP_PORT", None)

    def test_connect_and_command(self, live_instance):
        instance, port = live_instance

        # Connect as a client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(("localhost", port))

        # Send a command
        cmd = {"id": "test_e2e_1", "action": "get_session_state", "params": {}}
        client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

        # Simulate Live's main loop processing
        time.sleep(0.1)
        instance.update_display()

        # Read response
        data = client.recv(65536).decode("utf-8")
        response = json.loads(data.strip())

        assert response["id"] == "test_e2e_1"
        assert response["ok"] is True
        assert response["result"]["tempo"] == 120.0

        client.close()

    def test_multiple_commands_same_connection(self, live_instance):
        instance, port = live_instance

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(("localhost", port))

        for i in range(3):
            req_id = "multi_e2e_%d" % i
            cmd = {"id": req_id, "action": "get_session_state", "params": {}}
            client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

            time.sleep(0.05)
            instance.update_display()

            data = client.recv(65536).decode("utf-8")
            response = json.loads(data.strip())
            assert response["id"] == req_id
            assert response["ok"] is True

        client.close()

    def test_error_command(self, live_instance):
        instance, port = live_instance

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(("localhost", port))

        cmd = {"id": "err_1", "action": "nonexistent", "params": {}}
        client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

        time.sleep(0.1)
        instance.update_display()

        data = client.recv(65536).decode("utf-8")
        response = json.loads(data.strip())

        assert response["id"] == "err_1"
        assert response["ok"] is False
        assert "UNKNOWN_ACTION" in response["code"]

        client.close()

    def test_invalid_json_ignored(self, live_instance):
        instance, port = live_instance

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(("localhost", port))

        # Send garbage
        client.sendall(b"this is not json\n")
        time.sleep(0.05)

        # Send valid command after — should still work
        cmd = {"id": "after_garbage", "action": "get_session_state", "params": {}}
        client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

        time.sleep(0.1)
        instance.update_display()

        data = client.recv(65536).decode("utf-8")
        response = json.loads(data.strip())
        assert response["id"] == "after_garbage"
        assert response["ok"] is True

        client.close()

    def test_response_is_newline_terminated(self, live_instance):
        instance, port = live_instance

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(("localhost", port))

        cmd = {"id": "nl_test", "action": "get_session_state", "params": {}}
        client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

        time.sleep(0.1)
        instance.update_display()

        raw = client.recv(65536).decode("utf-8")
        assert raw.endswith("\n"), "Response must be newline-terminated"

        client.close()
