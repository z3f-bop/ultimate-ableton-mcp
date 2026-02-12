"""ableton_session — Global session state."""

import json
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_session(operation: str, bpm: float = 0, numerator: int = 0,
                    denominator: int = 0, start: float = 0, length: float = 0,
                    enabled: bool = False) -> str:
    """Global session state: tempo, time signature, loop, metronome, undo/redo.

    Operations:
    - get_state: Full snapshot (transport, tempo, time sig, loop, metronome, counts)
    - set_tempo: Set BPM (20-999). Params: bpm
    - set_time_signature: Params: numerator, denominator
    - set_loop: Loop region in beats. Params: start, length
    - set_metronome: Params: enabled (bool)
    - tap_tempo: Tap tempo
    - undo / redo: Undo/redo last action
    - set_arrangement_overdub: Params: enabled
    - set_session_automation_record: Params: enabled
    - re_enable_automation: Re-enable all automation
    """
    conn = get_connection()

    if operation == "get_state":
        result = conn.send("get_session_state")
        return json.dumps(result, indent=2)

    elif operation == "set_tempo":
        result = conn.send("set_tempo", {"bpm": bpm})
        return json.dumps(result)

    elif operation == "set_time_signature":
        result = conn.send("set_time_signature",
                          {"numerator": numerator, "denominator": denominator})
        return json.dumps(result)

    elif operation == "set_loop":
        result = conn.send("set_loop", {"start": start, "length": length})
        return json.dumps(result)

    elif operation == "set_metronome":
        result = conn.send("set_metronome", {"enabled": enabled})
        return json.dumps(result)

    elif operation == "tap_tempo":
        result = conn.send("tap_tempo")
        return json.dumps(result)

    elif operation == "undo":
        result = conn.send("undo")
        return json.dumps(result)

    elif operation == "redo":
        result = conn.send("redo")
        return json.dumps(result)

    elif operation == "set_arrangement_overdub":
        result = conn.send("set_arrangement_overdub", {"enabled": enabled})
        return json.dumps(result)

    elif operation == "set_session_automation_record":
        result = conn.send("set_session_automation_record", {"enabled": enabled})
        return json.dumps(result)

    elif operation == "re_enable_automation":
        result = conn.send("re_enable_automation")
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
