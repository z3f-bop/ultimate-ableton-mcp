"""ableton_scene — Scene management."""

import json
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_scene(operation: str, scene_index: int = 0, name: str = "",
                  color: int = 0, bpm: float = 0) -> str:
    """Scene management.

    Operations:
    - list: All scenes
    - get: Scene detail. Params: scene_index
    - create: New scene. Params: name?
    - delete / duplicate / fire: Params: scene_index
    - rename: Params: scene_index, name
    - set_color: Params: scene_index, color
    - set_tempo: Scene tempo. Params: scene_index, bpm
    """
    conn = get_connection()

    if operation == "list":
        result = conn.send("list_scenes")
        return json.dumps(result, indent=2)

    elif operation == "get":
        result = conn.send("get_scene", {"scene_index": scene_index})
        return json.dumps(result, indent=2)

    elif operation == "create":
        result = conn.send("create_scene", {"name": name})
        return json.dumps(result)

    elif operation == "delete":
        result = conn.send("delete_scene", {"scene_index": scene_index})
        return json.dumps(result)

    elif operation == "duplicate":
        result = conn.send("duplicate_scene", {"scene_index": scene_index})
        return json.dumps(result)

    elif operation == "fire":
        result = conn.send("fire_scene", {"scene_index": scene_index})
        return json.dumps(result)

    elif operation == "rename":
        result = conn.send("rename_scene",
                          {"scene_index": scene_index, "name": name})
        return json.dumps(result)

    elif operation == "set_color":
        result = conn.send("set_scene_color",
                          {"scene_index": scene_index, "color": color})
        return json.dumps(result)

    elif operation == "set_tempo":
        result = conn.send("set_scene_tempo",
                          {"scene_index": scene_index, "bpm": bpm})
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
