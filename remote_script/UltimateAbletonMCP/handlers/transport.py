"""Transport handler — playback and navigation."""


class TransportHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "start_playback": self._play,
            "stop_playback": self._stop,
            "continue_playback": self._continue,
            "set_record": self._record,
            "seek": self._seek,
            "jump_to_cue": self._jump_to_cue,
            "scroll_to_time": self._scroll_to_time,
            "show_view": self._show_view,
        }

    def _play(self, params):
        self._song.start_playing()
        return {"is_playing": self._song.is_playing}

    def _stop(self, params):
        self._song.stop_playing()
        return {"is_playing": self._song.is_playing}

    def _continue(self, params):
        self._song.continue_playing()
        return {"is_playing": self._song.is_playing}

    def _record(self, params):
        enabled = bool(params.get("enabled", False))
        self._song.record_mode = enabled
        if enabled and not self._song.is_playing:
            self._song.start_playing()
        return {"record_mode": self._song.record_mode}

    def _seek(self, params):
        time = float(params.get("time", 0))
        self._song.current_song_time = time
        return {"current_song_time": float(self._song.current_song_time)}

    def _jump_to_cue(self, params):
        direction = params.get("direction", "next")
        if direction == "next":
            self._song.jump_to_next_cue()
        else:
            self._song.jump_to_prev_cue()
        return {"current_song_time": float(self._song.current_song_time)}

    def _scroll_to_time(self, params):
        time = float(params.get("time", 0))
        self._song.current_song_time = time
        return {"scrolled_to": time}

    def _show_view(self, params):
        view = params.get("view", "session")
        app = self._c.application()
        view_map = {
            "session": app.View.Session,
            "arrangement": app.View.Arranger,
        }
        target = view_map.get(view)
        if target is not None:
            app.view.focus_view(target)
        return {"view": view}
