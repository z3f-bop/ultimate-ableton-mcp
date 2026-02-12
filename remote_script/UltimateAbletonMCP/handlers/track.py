"""Track handler — CRUD, mixing, routing."""


class TrackHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "list_tracks": self._list,
            "get_track": self._get,
            "create_track": self._create,
            "delete_track": self._delete,
            "duplicate_track": self._duplicate,
            "rename_track": self._rename,
            "set_track_volume": self._set_volume,
            "set_track_pan": self._set_pan,
            "set_track_mute": self._set_mute,
            "set_track_solo": self._set_solo,
            "set_track_arm": self._set_arm,
            "set_track_color": self._set_color,
            "set_track_send": self._set_send,
            "set_track_input_routing": self._set_input_routing,
            "set_track_output_routing": self._set_output_routing,
            "freeze_track": self._freeze,
            "flatten_track": self._flatten,
            "stop_track_clips": self._stop_all_clips,
        }

    def _get_track(self, index):
        tracks = self._song.tracks
        if index < 0 or index >= len(tracks):
            raise IndexError("Track index %d out of range (0-%d)" % (index, len(tracks) - 1))
        return tracks[index]

    def _track_info(self, track, index):
        devices = []
        for di, d in enumerate(track.devices):
            devices.append({"index": di, "name": d.name, "class_name": d.class_name})

        clip_slots = []
        for si, slot in enumerate(track.clip_slots):
            clip = None
            if slot.has_clip:
                c = slot.clip
                clip = {
                    "name": c.name,
                    "length": float(c.length),
                    "is_playing": c.is_playing,
                    "is_recording": c.is_recording,
                }
            clip_slots.append({"index": si, "has_clip": slot.has_clip, "clip": clip})

        sends = []
        for si, send in enumerate(track.mixer_device.sends):
            sends.append({"index": si, "value": float(send.value)})

        return {
            "index": index,
            "name": track.name,
            "type": "audio" if track.has_audio_input else "midi",
            "color": track.color,
            "arm": track.arm,
            "mute": track.mute,
            "solo": track.solo,
            "volume": float(track.mixer_device.volume.value),
            "pan": float(track.mixer_device.panning.value),
            "sends": sends,
            "devices": devices,
            "clip_slots": clip_slots,
        }

    def _list(self, params):
        tracks = []
        for i, t in enumerate(self._song.tracks):
            tracks.append({
                "index": i,
                "name": t.name,
                "type": "audio" if t.has_audio_input else "midi",
                "armed": t.arm,
                "muted": t.mute,
                "soloed": t.solo,
                "volume": float(t.mixer_device.volume.value),
            })
        return {"tracks": tracks, "count": len(tracks)}

    def _get(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        return self._track_info(track, idx)

    def _create(self, params):
        track_type = params.get("type", "midi")
        index = int(params.get("index", -1))

        if track_type == "midi":
            self._song.create_midi_track(index)
        elif track_type == "audio":
            self._song.create_audio_track(index)
        elif track_type == "return":
            self._song.create_return_track()
        else:
            raise ValueError("Unknown track type: %s" % track_type)

        new_idx = len(self._song.tracks) - 1 if index == -1 else index
        track = self._song.tracks[new_idx]

        name = params.get("name", "")
        if name:
            track.name = name

        return {"index": new_idx, "name": track.name, "type": track_type}

    def _delete(self, params):
        idx = int(params.get("track_index", 0))
        self._song.delete_track(idx)
        return {"deleted": idx}

    def _duplicate(self, params):
        idx = int(params.get("track_index", 0))
        self._song.duplicate_track(idx)
        return {"duplicated": idx, "new_index": idx + 1}

    def _rename(self, params):
        idx = int(params.get("track_index", 0))
        name = params.get("name", "")
        track = self._get_track(idx)
        track.name = name
        return {"index": idx, "name": track.name}

    def _set_volume(self, params):
        idx = int(params.get("track_index", 0))
        val = float(params.get("value", 0.85))
        track = self._get_track(idx)
        track.mixer_device.volume.value = max(0.0, min(1.0, val))
        return {"index": idx, "volume": float(track.mixer_device.volume.value)}

    def _set_pan(self, params):
        idx = int(params.get("track_index", 0))
        val = float(params.get("value", 0))
        track = self._get_track(idx)
        track.mixer_device.panning.value = max(-1.0, min(1.0, val))
        return {"index": idx, "pan": float(track.mixer_device.panning.value)}

    def _set_mute(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        track.mute = bool(params.get("enabled", False))
        return {"index": idx, "mute": track.mute}

    def _set_solo(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        track.solo = bool(params.get("enabled", False))
        return {"index": idx, "solo": track.solo}

    def _set_arm(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        track.arm = bool(params.get("enabled", False))
        return {"index": idx, "arm": track.arm}

    def _set_color(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        track.color = int(params.get("color", 0))
        return {"index": idx, "color": track.color}

    def _set_send(self, params):
        idx = int(params.get("track_index", 0))
        send_idx = int(params.get("send_index", 0))
        val = float(params.get("value", 0))
        track = self._get_track(idx)
        sends = track.mixer_device.sends
        if send_idx < 0 or send_idx >= len(sends):
            raise IndexError("Send index out of range")
        sends[send_idx].value = max(0.0, min(1.0, val))
        return {"index": idx, "send_index": send_idx,
                "value": float(sends[send_idx].value)}

    def _set_input_routing(self, params):
        idx = int(params.get("track_index", 0))
        routing_type = params.get("routing_type", "")
        track = self._get_track(idx)
        # Available input routing types and channels vary by setup
        available = list(track.available_input_routing_types)
        for rt in available:
            if rt.display_name == routing_type:
                track.input_routing_type = rt
                return {"index": idx, "input_routing": rt.display_name}
        return {"index": idx, "error": "Routing type not found",
                "available": [r.display_name for r in available]}

    def _set_output_routing(self, params):
        idx = int(params.get("track_index", 0))
        routing_type = params.get("routing_type", "")
        track = self._get_track(idx)
        available = list(track.available_output_routing_types)
        for rt in available:
            if rt.display_name == routing_type:
                track.output_routing_type = rt
                return {"index": idx, "output_routing": rt.display_name}
        return {"index": idx, "error": "Routing type not found",
                "available": [r.display_name for r in available]}

    def _freeze(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        if hasattr(track, "freeze_available") and not track.freeze_available:
            return {"index": idx, "frozen": False, "error": "Track cannot be frozen"}
        track.freeze()
        return {"index": idx, "frozen": True}

    def _flatten(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        if hasattr(track, "freeze_available") and not track.freeze_available:
            return {"index": idx, "flattened": False, "error": "Track cannot be flattened"}
        track.flatten()
        return {"index": idx, "flattened": True}

    def _stop_all_clips(self, params):
        idx = int(params.get("track_index", 0))
        track = self._get_track(idx)
        track.stop_all_clips()
        return {"index": idx, "stopped": True}
