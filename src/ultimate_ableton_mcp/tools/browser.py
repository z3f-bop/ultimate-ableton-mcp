"""ableton_browser — Content browser + groove pool."""

import json
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_browser(operation: str, category: str = "all", path: str = "",
                    track_index: int = 0, uri: str = "") -> str:
    """Content browser and groove pool.

    Operations:
    - get_tree: Browser category tree. Params: category? (instruments/sounds/drums/audio_effects/midi_effects/all)
    - get_items: Items at path. Params: path
    - load_item: Load onto track. Params: track_index, uri
    - get_grooves: List groove pool
    """
    conn = get_connection()

    if operation == "get_tree":
        result = conn.send("get_browser_tree", {"category": category})
        return json.dumps(result, indent=2)

    elif operation == "get_items":
        result = conn.send("get_browser_items", {"path": path})
        return json.dumps(result, indent=2)

    elif operation == "load_item":
        result = conn.send("load_browser_item",
                          {"track_index": track_index, "uri": uri})
        return json.dumps(result)

    elif operation == "get_grooves":
        result = conn.send("get_grooves")
        return json.dumps(result, indent=2)

    else:
        return f"Unknown operation: {operation}"
