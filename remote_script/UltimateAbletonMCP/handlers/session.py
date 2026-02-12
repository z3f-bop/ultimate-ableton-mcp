"""Session handler — global state operations."""


class SessionHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "get_session_state": self._get_state,
            "set_tempo": self._set_tempo,
            "set_time_signature": self._set_time_signature,
            "set_loop": self._set_loop,
            "set_metronome": self._set_metronome,
            "tap_tempo": self._tap_tempo,
            "undo": self._undo,
            "redo": self._redo,
            "set_arrangement_overdub": self._set_arrangement_overdub,
            "set_session_automation_record": self._set_session_automation_record,
            "re_enable_automation": self._re_enable_automation,
        }

    def _get_state(self, params):
        s = self._song
        tracks = []
        for i, t in enumerate(s.tracks):
            tracks.append({
                "index": i,
                "name": t.name,
                "type": "audio" if t.has_audio_input else "midi",
                "armed": t.arm,
                "muted": t.mute,
                "soloed": t.solo,
            })
        return_tracks = []
        for i, t in enumerate(s.return_tracks):
            return_tracks.append({"index": i, "name": t.name})
        scenes = []
        for i, sc in enumerate(s.scenes):
            scenes.append({"index": i, "name": sc.name})

        return {
            "tempo": float(s.tempo),
            "time_signature": "%d/%d" % (s.signature_numerator, s.signature_denominator),
            "signature_numerator": s.signature_numerator,
            "signature_denominator": s.signature_denominator,
            "is_playing": s.is_playing,
            "record_mode": s.record_mode,
            "metronome": s.metronome,
            "current_song_time": float(s.current_song_time),
            "loop_start": float(s.loop_start),
            "loop_length": float(s.loop_length),
            "track_count": len(s.tracks),
            "return_track_count": len(s.return_tracks),
            "scene_count": len(s.scenes),
            "tracks": tracks,
            "return_tracks": return_tracks,
            "scenes": scenes,
        }

    def _set_tempo(self, params):
        bpm = float(params.get("bpm", 120))
        if bpm < 20 or bpm > 999:
            raise ValueError("BPM must be between 20 and 999")
        self._song.tempo = bpm
        return {"tempo": float(self._song.tempo)}

    def _set_time_signature(self, params):
        num = int(params.get("numerator", 4))
        den = int(params.get("denominator", 4))
        if num < 1 or num > 99:
            raise ValueError("Numerator must be 1-99")
        if den not in (1, 2, 4, 8, 16):
            raise ValueError("Denominator must be 1, 2, 4, 8, or 16")
        self._song.signature_numerator = num
        self._song.signature_denominator = den
        return {"numerator": num, "denominator": den}

    def _set_loop(self, params):
        self._song.loop_start = float(params.get("start", 0))
        self._song.loop_length = float(params.get("length", 4))
        return {
            "loop_start": float(self._song.loop_start),
            "loop_length": float(self._song.loop_length),
        }

    def _set_metronome(self, params):
        self._song.metronome = bool(params.get("enabled", False))
        return {"metronome": self._song.metronome}

    def _tap_tempo(self, params):
        self._song.tap_tempo()
        return {"tempo": float(self._song.tempo)}

    def _undo(self, params):
        self._song.undo()
        return {"message": "Undo executed"}

    def _redo(self, params):
        self._song.redo()
        return {"message": "Redo executed"}

    def _set_arrangement_overdub(self, params):
        self._song.arrangement_overdub = bool(params.get("enabled", False))
        return {"arrangement_overdub": self._song.arrangement_overdub}

    def _set_session_automation_record(self, params):
        self._song.session_automation_record = bool(params.get("enabled", False))
        return {"session_automation_record": self._song.session_automation_record}

    def _re_enable_automation(self, params):
        self._song.re_enable_automation()
        return {"message": "Automation re-enabled"}
