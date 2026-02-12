"""UltimateAbletonMCP Remote Script for Ableton Live.

Per-request-ID queue architecture:
1. TCP socket thread receives newline-delimited JSON commands
2. Each command gets unique request_id, goes into command_queue
3. update_display() (Live main thread, every tick) drains queue, dispatches
4. Results go into response_queues[request_id]
5. Socket thread picks up response, sends back

No ControlSurface inheritance — raw Remote Script interface.
"""

from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import socket
import threading
import traceback

try:
    import Queue as queue  # Python 2 (Ableton < 12)
except ImportError:
    import queue  # Python 3 (Ableton 12+)

from .handlers.session import SessionHandler
from .handlers.transport import TransportHandler
from .handlers.track import TrackHandler
from .handlers.clip import ClipHandler
from .handlers.device import DeviceHandler
from .handlers.scene import SceneHandler
from .handlers.browser import BrowserHandler

HOST = "localhost"
DEFAULT_PORT = 9877


def create_instance(c_instance):
    """Entry point called by Ableton Live."""
    return UltimateAbletonMCP(c_instance)


class UltimateAbletonMCP(object):
    """Raw Remote Script — no ControlSurface dependency."""

    def __init__(self, c_instance):
        self._c_instance = c_instance
        self._song = c_instance.song()
        self._running = False
        self._server_socket = None
        self._server_thread = None
        self._client_threads = []

        # Per-request queuing
        self._command_queue = queue.Queue()
        self._response_queues = {}
        self._response_lock = threading.Lock()

        # Initialize handlers
        self._handlers = {
            "session": SessionHandler(self._song, c_instance),
            "transport": TransportHandler(self._song, c_instance),
            "track": TrackHandler(self._song, c_instance),
            "clip": ClipHandler(self._song, c_instance),
            "device": DeviceHandler(self._song, c_instance),
            "scene": SceneHandler(self._song, c_instance),
            "browser": BrowserHandler(self._song, c_instance),
        }

        # Action -> (handler_key, method_name) dispatch table
        self._dispatch = self._build_dispatch_table()

        self._start_server()
        self.log("UltimateAbletonMCP initialized")
        self._show_message("UltimateAbletonMCP ready on port %d" % self._port)

    @property
    def _port(self):
        try:
            return int(os.environ.get("ABLETON_MCP_PORT", DEFAULT_PORT))
        except (ValueError, TypeError):
            return DEFAULT_PORT

    def log(self, msg):
        self._c_instance.log_message("[UltimateAbletonMCP] " + str(msg))

    def _show_message(self, msg):
        self._c_instance.show_message(str(msg))

    def _build_dispatch_table(self):
        """Build action -> (handler, method) mapping from all handlers."""
        table = {}
        for handler in self._handlers.values():
            for action, method in handler.get_actions().items():
                table[action] = method
        return table

    # --- Server lifecycle ---

    def _start_server(self):
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((HOST, self._port))
            self._server_socket.listen(5)
            self._running = True

            self._server_thread = threading.Thread(target=self._accept_loop)
            self._server_thread.daemon = True
            self._server_thread.start()

            self.log("Server started on port %d" % self._port)
        except Exception as e:
            self.log("Error starting server: %s" % str(e))
            self._show_message("UltimateAbletonMCP: Server error - %s" % str(e))

    def disconnect(self):
        """Called by Ableton when script is removed or Live closes."""
        self.log("Disconnecting...")
        self._running = False

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(2.0)

        self.log("Disconnected")

    # --- Main thread: drain command queue ---

    def update_display(self):
        """Called by Live on every UI tick (~100ms). Drains the command queue."""
        try:
            while not self._command_queue.empty():
                try:
                    request_id, action, params = self._command_queue.get_nowait()
                except queue.Empty:
                    break

                response = self._execute(action, params)
                response["id"] = request_id

                with self._response_lock:
                    rq = self._response_queues.get(request_id)
                    if rq:
                        rq.put(response)
        except Exception as e:
            self.log("Error in update_display: %s" % str(e))

    def _execute(self, action, params):
        """Dispatch action to the appropriate handler method."""
        method = self._dispatch.get(action)
        if method is None:
            return {"ok": False, "error": "Unknown action: %s" % action,
                    "code": "UNKNOWN_ACTION"}
        try:
            result = method(params)
            return {"ok": True, "result": result}
        except Exception as e:
            self.log("Error executing %s: %s\n%s" % (
                action, str(e), traceback.format_exc()))
            return {"ok": False, "error": str(e), "code": "EXECUTION_ERROR"}

    # --- Socket threads ---

    def _accept_loop(self):
        self._server_socket.settimeout(1.0)
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                self.log("Client connected from %s" % str(addr))
                t = threading.Thread(target=self._handle_client, args=(client,))
                t.daemon = True
                t.start()
                self._client_threads.append(t)
                self._client_threads = [t for t in self._client_threads if t.is_alive()]
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    self.log("Accept error: %s" % str(e))

    def _handle_client(self, client):
        buffer = ""
        client.settimeout(None)
        try:
            while self._running:
                data = client.recv(65536)
                if not data:
                    break

                try:
                    buffer += data.decode("utf-8")
                except AttributeError:
                    buffer += data

                # Process all complete lines (newline-delimited JSON)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        command = json.loads(line)
                    except (ValueError, TypeError):
                        self.log("Invalid JSON: %s" % line[:200])
                        continue

                    request_id = command.get("id", "unknown")
                    action = command.get("action", "")
                    params = command.get("params", {})

                    # Create response queue for this request
                    rq = queue.Queue()
                    with self._response_lock:
                        self._response_queues[request_id] = rq

                    # Enqueue for main thread execution
                    self._command_queue.put((request_id, action, params))

                    # Wait for response (with timeout)
                    try:
                        response = rq.get(timeout=15.0)
                    except queue.Empty:
                        response = {
                            "id": request_id,
                            "ok": False,
                            "error": "Timeout waiting for Ableton to process command",
                            "code": "TIMEOUT",
                        }

                    # Cleanup
                    with self._response_lock:
                        self._response_queues.pop(request_id, None)

                    # Send response as newline-delimited JSON
                    resp_line = json.dumps(response) + "\n"
                    try:
                        client.sendall(resp_line.encode("utf-8"))
                    except Exception:
                        break

        except Exception as e:
            self.log("Client handler error: %s" % str(e))
        finally:
            try:
                client.close()
            except Exception:
                pass
            self.log("Client disconnected")
