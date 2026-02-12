"""Clip handler — session/arrangement clips and MIDI notes."""


class ClipHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "create_clip": self._create,
            "delete_clip": self._delete,
            "duplicate_clip": self._duplicate,
            "fire_clip": self._fire,
            "stop_clip": self._stop,
            "get_clip": self._get,
            "rename_clip": self._rename,
            "set_clip_loop": self._set_loop,
            "add_clip_notes": self._add_notes,
            "get_clip_notes": self._get_notes,
            "remove_clip_notes": self._remove_notes,
            "set_clip_notes": self._set_notes,
            "get_arrangement_clips": self._get_arrangement_clips,
            "duplicate_clip_to_arrangement": self._duplicate_to_arrangement,
            "set_clip_groove": self._set_groove,
            "stop_all_clips": self._stop_all,
        }

    def _get_slot(self, params):
        ti = int(params.get("track_index", 0))
        si = int(params.get("scene_index", 0))
        tracks = self._song.tracks
        if ti < 0 or ti >= len(tracks):
            raise IndexError("Track index %d out of range" % ti)
        track = tracks[ti]
        slots = track.clip_slots
        if si < 0 or si >= len(slots):
            raise IndexError("Scene index %d out of range" % si)
        return track, slots[si], ti, si

    def _create(self, params):
        track, slot, ti, si = self._get_slot(params)
        length = float(params.get("length", 4.0))
        if slot.has_clip:
            raise RuntimeError("Clip slot already has a clip")
        slot.create_clip(length)
        return {"track_index": ti, "scene_index": si,
                "name": slot.clip.name, "length": float(slot.clip.length)}

    def _delete(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        slot.delete_clip()
        return {"deleted": True, "track_index": ti, "scene_index": si}

    def _duplicate(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        slot.duplicate_clip_to(track.clip_slots[si + 1] if si + 1 < len(track.clip_slots) else slot)
        return {"duplicated": True}

    def _fire(self, params):
        track, slot, ti, si = self._get_slot(params)
        slot.fire()
        return {"fired": True}

    def _stop(self, params):
        track, slot, ti, si = self._get_slot(params)
        slot.stop()
        return {"stopped": True}

    def _get(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            return {"has_clip": False, "track_index": ti, "scene_index": si}
        c = slot.clip
        return {
            "has_clip": True,
            "track_index": ti,
            "scene_index": si,
            "name": c.name,
            "length": float(c.length),
            "is_playing": c.is_playing,
            "is_recording": c.is_recording,
            "loop_start": float(c.loop_start),
            "loop_end": float(c.loop_end),
            "start_marker": float(c.start_marker),
            "end_marker": float(c.end_marker),
        }

    def _rename(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        slot.clip.name = params.get("name", "")
        return {"name": slot.clip.name}

    def _set_loop(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        clip = slot.clip
        clip.loop_start = float(params.get("start", 0))
        clip.loop_end = float(params.get("end", 4))
        return {"loop_start": float(clip.loop_start),
                "loop_end": float(clip.loop_end)}

    # --- MIDI Notes (Live 12 extended API with legacy fallback) ---

    def _build_note_tuple(self, n):
        """Build a (pitch, start, duration, velocity, mute) tuple from note dict."""
        pitch = int(n.get("pitch", 60))
        start = float(n.get("start", 0))
        duration = float(n.get("duration", 0.25))
        velocity = int(n.get("velocity", 100))
        mute = bool(n.get("mute", False))
        return (pitch, start, duration, velocity, mute)

    def _add_notes(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        clip = slot.clip
        notes = params.get("notes", [])
        live_notes = [self._build_note_tuple(n) for n in notes]
        # Legacy API — works on all Live versions
        clip.set_notes(tuple(live_notes))
        return {"added": len(live_notes)}

    def _get_notes(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        clip = slot.clip

        # Try Live 12 extended API first (keyword args)
        if hasattr(clip, "get_notes_extended"):
            notes_raw = clip.get_notes_extended(
                from_time=0.0,
                from_pitch=0,
                time_span=float(clip.length),
                pitch_span=128
            )
        else:
            # Legacy: get_notes(from_time, from_pitch, time_span, pitch_span)
            notes_raw = clip.get_notes(0.0, 0, float(clip.length), 128)

        notes = []
        for n in notes_raw:
            notes.append({
                "pitch": n[0],
                "start": float(n[1]),
                "duration": float(n[2]),
                "velocity": n[3],
                "mute": n[4] if len(n) > 4 else False,
            })
        return {"notes": notes, "count": len(notes)}

    def _remove_notes(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        clip = slot.clip

        if hasattr(clip, "remove_notes_extended"):
            clip.remove_notes_extended(
                from_pitch=0,
                pitch_span=128,
                from_time=0.0,
                time_span=float(clip.length)
            )
        else:
            # Legacy: remove_notes(from_time, from_pitch, time_span, pitch_span)
            clip.remove_notes(0.0, 0, float(clip.length), 128)
        return {"removed": True}

    def _set_notes(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        clip = slot.clip

        # Clear existing notes
        if hasattr(clip, "remove_notes_extended"):
            clip.remove_notes_extended(
                from_pitch=0, pitch_span=128,
                from_time=0.0, time_span=float(clip.length)
            )
        else:
            clip.remove_notes(0.0, 0, float(clip.length), 128)

        # Add new ones
        notes = params.get("notes", [])
        live_notes = [self._build_note_tuple(n) for n in notes]
        if live_notes:
            clip.set_notes(tuple(live_notes))
        return {"set": len(live_notes)}

    # --- Arrangement ---

    def _get_arrangement_clips(self, params):
        ti = int(params.get("track_index", 0))
        tracks = self._song.tracks
        if ti < 0 or ti >= len(tracks):
            raise IndexError("Track index out of range")
        track = tracks[ti]
        clips = []
        if hasattr(track, "arrangement_clips"):
            for c in track.arrangement_clips:
                clips.append({
                    "name": c.name,
                    "start_time": float(c.start_time),
                    "end_time": float(c.end_time),
                    "length": float(c.length),
                })
        return {"clips": clips, "count": len(clips)}

    def _duplicate_to_arrangement(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        self._song.view.selected_track = track
        slot.fire()
        return {"message": "Clip fired for arrangement capture"}

    def _set_groove(self, params):
        track, slot, ti, si = self._get_slot(params)
        if not slot.has_clip:
            raise RuntimeError("No clip in slot")
        groove_idx = int(params.get("groove_index", 0))
        pool = self._song.groove_pool
        if hasattr(pool, "grooves"):
            grooves = list(pool.grooves)
            if groove_idx < len(grooves):
                slot.clip.groove = grooves[groove_idx]
                return {"groove_set": True}
        return {"groove_set": False, "error": "Groove not found"}

    def _stop_all(self, params):
        quantized = int(params.get("quantized", 1))
        self._song.stop_all_clips(quantized)
        return {"stopped_all": True}
