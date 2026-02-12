"""ableton_track — CRUD, mix, routing."""

import json
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_track(operation: str, track_index: int = -1, type: str = "midi",
                  name: str = "", index: int = -1, value: float = 0,
                  send_index: int = 0, routing_type: str = "",
                  channel: str = "", color: int = 0,
                  enabled: bool = False) -> str:
    """Track CRUD, mixing, and routing.

    Operations:
    - list: All tracks summary
    - get: Single track detail. Params: track_index
    - create: New track. Params: type (midi/audio/return), name?, index?
    - delete / duplicate: Params: track_index
    - rename: Params: track_index, name
    - set_volume / set_pan: Params: track_index, value (0.0-1.0)
    - set_mute / set_solo / set_arm: Params: track_index, enabled
    - set_color: Params: track_index, color (int)
    - set_send: Params: track_index, send_index, value
    - set_input_routing / set_output_routing: Params: track_index, routing_type, channel?
    - freeze / flatten: Params: track_index
    - stop_all_clips: Params: track_index
    """
    conn = get_connection()

    if operation == "list":
        result = conn.send("list_tracks")
        return json.dumps(result, indent=2)

    elif operation == "get":
        result = conn.send("get_track", {"track_index": track_index})
        return json.dumps(result, indent=2)

    elif operation == "create":
        result = conn.send("create_track",
                          {"type": type, "name": name, "index": index})
        return json.dumps(result)

    elif operation == "delete":
        result = conn.send("delete_track", {"track_index": track_index})
        return json.dumps(result)

    elif operation == "duplicate":
        result = conn.send("duplicate_track", {"track_index": track_index})
        return json.dumps(result)

    elif operation == "rename":
        result = conn.send("rename_track",
                          {"track_index": track_index, "name": name})
        return json.dumps(result)

    elif operation == "set_volume":
        result = conn.send("set_track_volume",
                          {"track_index": track_index, "value": value})
        return json.dumps(result)

    elif operation == "set_pan":
        result = conn.send("set_track_pan",
                          {"track_index": track_index, "value": value})
        return json.dumps(result)

    elif operation == "set_mute":
        result = conn.send("set_track_mute",
                          {"track_index": track_index, "enabled": enabled})
        return json.dumps(result)

    elif operation == "set_solo":
        result = conn.send("set_track_solo",
                          {"track_index": track_index, "enabled": enabled})
        return json.dumps(result)

    elif operation == "set_arm":
        result = conn.send("set_track_arm",
                          {"track_index": track_index, "enabled": enabled})
        return json.dumps(result)

    elif operation == "set_color":
        result = conn.send("set_track_color",
                          {"track_index": track_index, "color": color})
        return json.dumps(result)

    elif operation == "set_send":
        result = conn.send("set_track_send",
                          {"track_index": track_index,
                           "send_index": send_index, "value": value})
        return json.dumps(result)

    elif operation == "set_input_routing":
        result = conn.send("set_track_input_routing",
                          {"track_index": track_index,
                           "routing_type": routing_type, "channel": channel})
        return json.dumps(result)

    elif operation == "set_output_routing":
        result = conn.send("set_track_output_routing",
                          {"track_index": track_index,
                           "routing_type": routing_type, "channel": channel})
        return json.dumps(result)

    elif operation == "freeze":
        result = conn.send("freeze_track", {"track_index": track_index})
        return json.dumps(result)

    elif operation == "flatten":
        result = conn.send("flatten_track", {"track_index": track_index})
        return json.dumps(result)

    elif operation == "stop_all_clips":
        result = conn.send("stop_track_clips", {"track_index": track_index})
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
