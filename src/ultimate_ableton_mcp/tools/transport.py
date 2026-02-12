"""ableton_transport — Playback & navigation."""

import json
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_transport(operation: str, enabled: bool = False, time: float = 0,
                      direction: str = "next", view: str = "session") -> str:
    """Playback control and navigation.

    Operations:
    - play / stop / continue: Transport control
    - record: Toggle recording. Params: enabled
    - seek: Jump to position. Params: time (beats)
    - jump_to_cue: Next/prev cue point. Params: direction (next/prev)
    - scroll_to_time: Scroll view. Params: time
    - show_view: Switch view. Params: view (session/arrangement/clip)
    """
    conn = get_connection()

    if operation == "play":
        result = conn.send("start_playback")
        return json.dumps(result)

    elif operation == "stop":
        result = conn.send("stop_playback")
        return json.dumps(result)

    elif operation == "continue":
        result = conn.send("continue_playback")
        return json.dumps(result)

    elif operation == "record":
        result = conn.send("set_record", {"enabled": enabled})
        return json.dumps(result)

    elif operation == "seek":
        result = conn.send("seek", {"time": time})
        return json.dumps(result)

    elif operation == "jump_to_cue":
        result = conn.send("jump_to_cue", {"direction": direction})
        return json.dumps(result)

    elif operation == "scroll_to_time":
        result = conn.send("scroll_to_time", {"time": time})
        return json.dumps(result)

    elif operation == "show_view":
        result = conn.send("show_view", {"view": view})
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
