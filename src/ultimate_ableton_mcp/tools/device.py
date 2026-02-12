"""ableton_device — Parameters, presets, automation, racks."""

import json
from typing import Any
from ..server import mcp
from ..connection import get_connection


@mcp.tool()
def ableton_device(operation: str, track_index: int = 0,
                   device_index: int = 0, param: str | int = 0,
                   value: float = 0, enabled: bool = True,
                   preset_index: int = 0, clip_index: int = 0,
                   param_index: int = 0, time: float = 0) -> str:
    """Device parameters, presets, automation, and rack chains.

    Operations:
    - list: All devices on track. Params: track_index
    - get: Device detail. Params: track_index, device_index
    - get_param: Read parameter. Params: track_index, device_index, param (index or name)
    - set_param: Write parameter. Params: track_index, device_index, param, value
    - set_enabled: Enable/disable. Params: track_index, device_index, enabled
    - get_presets / set_preset: Params: track_index, device_index, preset_index?
    - get_chains: Rack chains. Params: track_index, device_index
    - get_automation: Params: track_index, clip_index, device_index, param_index
    - create_automation: Params: track_index, clip_index, device_index, param_index
    - clear_automation: Params: track_index, clip_index, device_index, param_index
    - insert_automation_point: Params: track_index, clip_index, device_index, param_index, time, value
    - remove_automation_point: Params: track_index, clip_index, device_index, param_index, time
    """
    conn = get_connection()
    dev_ref = {"track_index": track_index, "device_index": device_index}

    if operation == "list":
        result = conn.send("list_devices", {"track_index": track_index})
        return json.dumps(result, indent=2)

    elif operation == "get":
        result = conn.send("get_device", dev_ref)
        return json.dumps(result, indent=2)

    elif operation == "get_param":
        result = conn.send("get_device_param", {**dev_ref, "param": param})
        return json.dumps(result)

    elif operation == "set_param":
        result = conn.send("set_device_param",
                          {**dev_ref, "param": param, "value": value})
        return json.dumps(result)

    elif operation == "set_enabled":
        result = conn.send("set_device_enabled",
                          {**dev_ref, "enabled": enabled})
        return json.dumps(result)

    elif operation == "get_presets":
        result = conn.send("get_device_presets", dev_ref)
        return json.dumps(result, indent=2)

    elif operation == "set_preset":
        result = conn.send("set_device_preset",
                          {**dev_ref, "preset_index": preset_index})
        return json.dumps(result)

    elif operation == "get_chains":
        result = conn.send("get_device_chains", dev_ref)
        return json.dumps(result, indent=2)

    elif operation == "get_automation":
        auto_ref = {**dev_ref, "clip_index": clip_index,
                    "param_index": param_index}
        result = conn.send("get_automation", auto_ref)
        return json.dumps(result, indent=2)

    elif operation == "create_automation":
        auto_ref = {**dev_ref, "clip_index": clip_index,
                    "param_index": param_index}
        result = conn.send("create_automation", auto_ref)
        return json.dumps(result)

    elif operation == "clear_automation":
        auto_ref = {**dev_ref, "clip_index": clip_index,
                    "param_index": param_index}
        result = conn.send("clear_automation", auto_ref)
        return json.dumps(result)

    elif operation == "insert_automation_point":
        auto_ref = {**dev_ref, "clip_index": clip_index,
                    "param_index": param_index, "time": time, "value": value}
        result = conn.send("insert_automation_point", auto_ref)
        return json.dumps(result)

    elif operation == "remove_automation_point":
        auto_ref = {**dev_ref, "clip_index": clip_index,
                    "param_index": param_index, "time": time}
        result = conn.send("remove_automation_point", auto_ref)
        return json.dumps(result)

    else:
        return f"Unknown operation: {operation}"
