"""Scene handler — scene management."""


class SceneHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "list_scenes": self._list,
            "get_scene": self._get,
            "create_scene": self._create,
            "delete_scene": self._delete,
            "duplicate_scene": self._duplicate,
            "fire_scene": self._fire,
            "rename_scene": self._rename,
            "set_scene_color": self._set_color,
            "set_scene_tempo": self._set_tempo,
        }

    def _get_scene(self, index):
        scenes = self._song.scenes
        if index < 0 or index >= len(scenes):
            raise IndexError("Scene index %d out of range (0-%d)" % (index, len(scenes) - 1))
        return scenes[index]

    def _list(self, params):
        scenes = []
        for i, s in enumerate(self._song.scenes):
            scenes.append({
                "index": i,
                "name": s.name,
                "color": s.color,
                "tempo": float(s.tempo) if hasattr(s, "tempo") and s.tempo else None,
            })
        return {"scenes": scenes, "count": len(scenes)}

    def _get(self, params):
        idx = int(params.get("scene_index", 0))
        s = self._get_scene(idx)
        clip_info = []
        for ti, track in enumerate(self._song.tracks):
            slot = track.clip_slots[idx]
            clip = None
            if slot.has_clip:
                c = slot.clip
                clip = {"name": c.name, "is_playing": c.is_playing}
            clip_info.append({"track_index": ti, "has_clip": slot.has_clip, "clip": clip})
        return {
            "index": idx,
            "name": s.name,
            "color": s.color,
            "clips": clip_info,
        }

    def _create(self, params):
        idx = len(self._song.scenes)
        self._song.create_scene(idx)
        scene = self._song.scenes[idx]
        name = params.get("name", "")
        if name:
            scene.name = name
        return {"index": idx, "name": scene.name}

    def _delete(self, params):
        idx = int(params.get("scene_index", 0))
        self._song.delete_scene(idx)
        return {"deleted": idx}

    def _duplicate(self, params):
        idx = int(params.get("scene_index", 0))
        self._song.duplicate_scene(idx)
        return {"duplicated": idx}

    def _fire(self, params):
        idx = int(params.get("scene_index", 0))
        scene = self._get_scene(idx)
        scene.fire()
        return {"fired": idx}

    def _rename(self, params):
        idx = int(params.get("scene_index", 0))
        scene = self._get_scene(idx)
        scene.name = params.get("name", "")
        return {"index": idx, "name": scene.name}

    def _set_color(self, params):
        idx = int(params.get("scene_index", 0))
        scene = self._get_scene(idx)
        scene.color = int(params.get("color", 0))
        return {"index": idx, "color": scene.color}

    def _set_tempo(self, params):
        idx = int(params.get("scene_index", 0))
        scene = self._get_scene(idx)
        bpm = float(params.get("bpm", 0))
        if hasattr(scene, "tempo"):
            if bpm > 0 and hasattr(scene, "tempo_enabled"):
                scene.tempo_enabled = True
            scene.tempo = bpm
            return {"index": idx, "tempo": float(scene.tempo)}
        return {"index": idx, "error": "Scene tempo not supported in this Live version"}
