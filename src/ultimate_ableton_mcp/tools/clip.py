"""ableton_clip — Session + arrangement clips, MIDI notes."""

import json
from typing import Any
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_clip(operation: str, track_index: int = 0, scene_index: int = 0,
                 name: str = "", length: float = 4.0, start: float = 0,
                 end: float = 4.0, notes: list[dict[str, Any]] | None = None,
                 groove_index: int = 0) -> str:
    """Session/arrangement clip operations and MIDI note editing.

    Operations:
    - create: New clip. Params: track_index, scene_index, length?
    - delete / duplicate / fire / stop: Params: track_index, scene_index
    - get: Clip info. Params: track_index, scene_index
    - rename: Params: track_index, scene_index, name
    - set_loop: Params: track_index, scene_index, start, end
    - add_notes: Params: track_index, scene_index, notes (list of {pitch, start, duration, velocity})
    - get_notes: Params: track_index, scene_index
    - remove_notes: Params: track_index, scene_index, notes (list of {pitch, start, duration})
    - set_notes: Replace all notes. Params: track_index, scene_index, notes
    - get_arrangement_clips: Params: track_index
    - duplicate_to_arrangement: Params: track_index, scene_index
    - set_groove: Params: track_index, scene_index, groove_index
    - stop_all: Stop all clips globally
    """
    conn = get_connection()
    clip_ref = {"track_index": track_index, "scene_index": scene_index}

    if operation == "create":
        result = conn.send("create_clip", {**clip_ref, "length": length})
        return json.dumps(result)

    elif operation == "delete":
        result = conn.send("delete_clip", clip_ref)
        return json.dumps(result)

    elif operation == "duplicate":
        result = conn.send("duplicate_clip", clip_ref)
        return json.dumps(result)

    elif operation == "fire":
        result = conn.send("fire_clip", clip_ref)
        return json.dumps(result)

    elif operation == "stop":
        result = conn.send("stop_clip", clip_ref)
        return json.dumps(result)

    elif operation == "get":
        result = conn.send("get_clip", clip_ref)
        return json.dumps(result, indent=2)

    elif operation == "rename":
        result = conn.send("rename_clip", {**clip_ref, "name": name})
        return json.dumps(result)

    elif operation == "set_loop":
        result = conn.send("set_clip_loop",
                          {**clip_ref, "start": start, "end": end})
        return json.dumps(result)

    elif operation == "add_notes":
        result = conn.send("add_clip_notes",
                          {**clip_ref, "notes": notes or []})
        return json.dumps(result)

    elif operation == "get_notes":
        result = conn.send("get_clip_notes", clip_ref)
        return json.dumps(result, indent=2)

    elif operation == "remove_notes":
        result = conn.send("remove_clip_notes",
                          {**clip_ref, "notes": notes or []})
        return json.dumps(result)

    elif operation == "set_notes":
        result = conn.send("set_clip_notes",
                          {**clip_ref, "notes": notes or []})
        return json.dumps(result)

    elif operation == "get_arrangement_clips":
        result = conn.send("get_arrangement_clips",
                          {"track_index": track_index})
        return json.dumps(result, indent=2)

    elif operation == "duplicate_to_arrangement":
        result = conn.send("duplicate_clip_to_arrangement", clip_ref)
        return json.dumps(result)

    elif operation == "set_groove":
        result = conn.send("set_clip_groove",
                          {**clip_ref, "groove_index": groove_index})
        return json.dumps(result)

    elif operation == "stop_all":
        result = conn.send("stop_all_clips")
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
