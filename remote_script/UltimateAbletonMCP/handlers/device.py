"""Device handler — parameters, presets, automation, racks."""


class DeviceHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "list_devices": self._list,
            "get_device": self._get,
            "get_device_param": self._get_param,
            "set_device_param": self._set_param,
            "set_device_enabled": self._set_enabled,
            "get_device_presets": self._get_presets,
            "set_device_preset": self._set_preset,
            "get_device_chains": self._get_chains,
            "get_automation": self._get_automation,
            "create_automation": self._create_automation,
            "clear_automation": self._clear_automation,
            "insert_automation_point": self._insert_automation_point,
            "remove_automation_point": self._remove_automation_point,
        }

    def _get_track(self, index):
        tracks = self._song.tracks
        if index < 0 or index >= len(tracks):
            raise IndexError("Track index out of range")
        return tracks[index]

    def _get_device_obj(self, params):
        ti = int(params.get("track_index", 0))
        di = int(params.get("device_index", 0))
        track = self._get_track(ti)
        devices = track.devices
        if di < 0 or di >= len(devices):
            raise IndexError("Device index %d out of range" % di)
        return track, devices[di]

    def _list(self, params):
        ti = int(params.get("track_index", 0))
        track = self._get_track(ti)
        devices = []
        for di, d in enumerate(track.devices):
            devices.append({
                "index": di,
                "name": d.name,
                "class_name": d.class_name,
                "is_active": d.is_active,
            })
        return {"devices": devices, "count": len(devices)}

    def _get(self, params):
        track, device = self._get_device_obj(params)
        parameters = []
        for pi, p in enumerate(device.parameters):
            parameters.append({
                "index": pi,
                "name": p.name,
                "value": float(p.value),
                "min": float(p.min),
                "max": float(p.max),
                "default": float(p.default_value),
                "is_quantized": p.is_quantized,
            })
        return {
            "name": device.name,
            "class_name": device.class_name,
            "is_active": device.is_active,
            "can_have_chains": device.can_have_chains,
            "can_have_drum_pads": device.can_have_drum_pads,
            "parameters": parameters,
        }

    def _get_param(self, params):
        track, device = self._get_device_obj(params)
        param_ref = params.get("param", 0)
        param = self._resolve_param(device, param_ref)
        return {
            "name": param.name,
            "value": float(param.value),
            "min": float(param.min),
            "max": float(param.max),
        }

    def _set_param(self, params):
        track, device = self._get_device_obj(params)
        param_ref = params.get("param", 0)
        value = float(params.get("value", 0))
        param = self._resolve_param(device, param_ref)
        clamped = max(float(param.min), min(float(param.max), value))
        param.value = clamped
        return {"name": param.name, "value": float(param.value)}

    def _resolve_param(self, device, param_ref):
        """Resolve param by index (int) or name (str)."""
        if isinstance(param_ref, int) or (isinstance(param_ref, str) and param_ref.isdigit()):
            idx = int(param_ref)
            params = device.parameters
            if idx < 0 or idx >= len(params):
                raise IndexError("Parameter index out of range")
            return params[idx]
        else:
            name = str(param_ref).lower()
            for p in device.parameters:
                if p.name.lower() == name:
                    return p
            raise ValueError("Parameter '%s' not found" % param_ref)

    def _set_enabled(self, params):
        track, device = self._get_device_obj(params)
        # Device on/off is parameter 0 in most devices
        device.parameters[0].value = 1.0 if params.get("enabled", True) else 0.0
        return {"enabled": device.is_active}

    def _get_presets(self, params):
        track, device = self._get_device_obj(params)
        presets = []
        if hasattr(device, "presets"):
            for i, p in enumerate(device.presets):
                presets.append({"index": i, "name": str(p)})
        return {"presets": presets}

    def _set_preset(self, params):
        track, device = self._get_device_obj(params)
        idx = int(params.get("preset_index", 0))
        if hasattr(device, "selected_preset_index"):
            device.selected_preset_index = idx
            return {"preset_index": idx}
        return {"error": "Device does not support preset selection"}

    def _get_chains(self, params):
        track, device = self._get_device_obj(params)
        if not device.can_have_chains:
            return {"chains": [], "error": "Device is not a rack"}
        chains = []
        for ci, chain in enumerate(device.chains):
            chain_devices = []
            for di, d in enumerate(chain.devices):
                chain_devices.append({"index": di, "name": d.name})
            chains.append({
                "index": ci,
                "name": chain.name,
                "devices": chain_devices,
            })
        return {"chains": chains}

    # --- Automation ---

    def _get_clip_and_envelope(self, params):
        ti = int(params.get("track_index", 0))
        ci = int(params.get("clip_index", 0))
        di = int(params.get("device_index", 0))
        pi = int(params.get("param_index", 0))

        track = self._get_track(ti)
        slot = track.clip_slots[ci]
        if not slot.has_clip:
            raise RuntimeError("No clip in slot %d" % ci)
        clip = slot.clip
        device = track.devices[di]
        param = device.parameters[pi]
        return clip, param

    def _get_automation(self, params):
        clip, param = self._get_clip_and_envelope(params)
        envelope = clip.automation_envelope(param)
        if envelope is None:
            return {"has_automation": False}
        # Can't easily iterate envelope points in older API
        return {"has_automation": True, "param_name": param.name}

    def _create_automation(self, params):
        clip, param = self._get_clip_and_envelope(params)
        clip.create_automation_envelope(param)
        return {"created": True, "param_name": param.name}

    def _clear_automation(self, params):
        clip, param = self._get_clip_and_envelope(params)
        clip.clear_envelope(param)
        return {"cleared": True, "param_name": param.name}

    def _insert_automation_point(self, params):
        clip, param = self._get_clip_and_envelope(params)
        time = float(params.get("time", 0))
        value = float(params.get("value", 0))
        envelope = clip.automation_envelope(param)
        if envelope is None:
            clip.create_automation_envelope(param)
            envelope = clip.automation_envelope(param)
        envelope.insert_step(time, 0.0, value)
        return {"inserted": True, "time": time, "value": value}

    def _remove_automation_point(self, params):
        clip, param = self._get_clip_and_envelope(params)
        time = float(params.get("time", 0))
        envelope = clip.automation_envelope(param)
        if envelope is None:
            return {"removed": False, "error": "No automation envelope"}
        # Clear a small region around the point
        envelope.insert_step(time, 0.01, float(param.value))
        return {"removed": True, "time": time}
