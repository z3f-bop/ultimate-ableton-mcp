"""Mock Ableton Live Object Model (LOM) for testing.

Extracted from conftest.py so test modules can import directly.
"""

from unittest.mock import MagicMock


class MockParam:
    """Simulates a Live DeviceParameter."""

    def __init__(self, name="Volume", value=0.85, min_val=0.0, max_val=1.0,
                 default=0.85, quantized=False):
        self.name = name
        self.value = value
        self.min = min_val
        self.max = max_val
        self.default_value = default
        self.is_quantized = quantized


class MockMixerDevice:
    """Simulates a Live MixerDevice."""

    def __init__(self):
        self.volume = MockParam("Volume", 0.85, 0.0, 1.0)
        self.panning = MockParam("Pan", 0.0, -1.0, 1.0)
        self.sends = [MockParam("Send A", 0.0), MockParam("Send B", 0.0)]


class MockDevice:
    """Simulates a Live Device."""

    def __init__(self, name="Simpler", class_name="OriginalSimpler"):
        self.name = name
        self.class_name = class_name
        self.class_display_name = name
        self.is_active = True
        self.can_have_chains = False
        self.can_have_drum_pads = False
        self.chains = []
        self.parameters = [
            MockParam("Device On", 1.0, 0.0, 1.0),
            MockParam("Volume", 0.85, 0.0, 1.0),
            MockParam("Filter Freq", 1000.0, 20.0, 20000.0, default=1000.0),
        ]
        self.presets = ["Init", "Bass", "Pad"]
        self.selected_preset_index = 0


class MockClip:
    """Simulates a Live Clip."""

    def __init__(self, name="Clip", length=4.0):
        self.name = name
        self.length = length
        self.is_playing = False
        self.is_recording = False
        self.loop_start = 0.0
        self.loop_end = length
        self.start_marker = 0.0
        self.end_marker = length
        self._notes = []
        self._envelopes = {}

    def set_notes(self, notes):
        self._notes.extend(notes)

    def get_notes(self, start, pitch_start, length, pitch_span):
        return tuple(self._notes)

    def remove_notes(self, start, pitch_start, length, pitch_span):
        self._notes.clear()

    def automation_envelope(self, param):
        return self._envelopes.get(param.name)

    def create_automation_envelope(self, param):
        env = MockEnvelope()
        self._envelopes[param.name] = env
        return env

    def clear_envelope(self, param):
        self._envelopes.pop(param.name, None)


class MockEnvelope:
    """Simulates a Live AutomationEnvelope."""

    def __init__(self):
        self.points = []

    def insert_step(self, time, duration, value):
        self.points.append((time, duration, value))


class MockClipSlot:
    """Simulates a Live ClipSlot."""

    def __init__(self, has_clip=False, clip=None):
        self.has_clip = has_clip
        self.clip = clip
        self._fired = False
        self._stopped = False

    def create_clip(self, length):
        self.clip = MockClip(length=length)
        self.has_clip = True

    def delete_clip(self):
        self.clip = None
        self.has_clip = False

    def fire(self):
        self._fired = True

    def stop(self):
        self._stopped = True

    def duplicate_clip_to(self, target):
        if self.clip:
            target.clip = MockClip(name=self.clip.name + " Copy", length=self.clip.length)
            target.has_clip = True


class MockRoutingType:
    """Simulates a routing type."""

    def __init__(self, name):
        self.display_name = name


class MockTrack:
    """Simulates a Live Track."""

    def __init__(self, name="Track 1", is_midi=True, num_scenes=8):
        self.name = name
        self.has_audio_input = not is_midi
        self.has_midi_input = is_midi
        self.arm = False
        self.mute = False
        self.solo = False
        self.color = 0
        self.mixer_device = MockMixerDevice()
        self.devices = [MockDevice()]
        self.clip_slots = [MockClipSlot() for _ in range(num_scenes)]
        self.available_input_routing_types = [
            MockRoutingType("All Ins"),
            MockRoutingType("Computer Keyboard"),
        ]
        self.available_output_routing_types = [
            MockRoutingType("Master"),
            MockRoutingType("Sends Only"),
        ]
        self.input_routing_type = self.available_input_routing_types[0]
        self.output_routing_type = self.available_output_routing_types[0]

    def stop_all_clips(self):
        pass

    def freeze(self):
        pass

    def flatten(self):
        pass


class MockScene:
    """Simulates a Live Scene."""

    def __init__(self, name="Scene 1"):
        self.name = name
        self.color = 0
        self.tempo = 0.0
        self._fired = False

    def fire(self):
        self._fired = True


class MockGroovePool:
    """Simulates groove pool."""

    def __init__(self):
        self.grooves = []


class MockView:
    """Simulates Song.View."""

    def __init__(self):
        self.selected_track = None


class MockSong:
    """Simulates a Live Song."""

    def __init__(self):
        self.tempo = 120.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.is_playing = False
        self.record_mode = False
        self.metronome = False
        self.current_song_time = 0.0
        self.loop_start = 0.0
        self.loop_length = 4.0
        self.arrangement_overdub = False
        self.session_automation_record = False
        self.tracks = [MockTrack("Track 1", is_midi=True),
                       MockTrack("Track 2", is_midi=False)]
        self.return_tracks = [MockTrack("Return A")]
        self.scenes = [MockScene("Scene 1"), MockScene("Scene 2")]
        self.groove_pool = MockGroovePool()
        self.view = MockView()

    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def continue_playing(self):
        self.is_playing = True

    def tap_tempo(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def re_enable_automation(self):
        pass

    def stop_all_clips(self):
        pass

    def create_midi_track(self, index=-1):
        t = MockTrack("New MIDI", is_midi=True)
        if index == -1:
            self.tracks.append(t)
        else:
            self.tracks.insert(index, t)

    def create_audio_track(self, index=-1):
        t = MockTrack("New Audio", is_midi=False)
        if index == -1:
            self.tracks.append(t)
        else:
            self.tracks.insert(index, t)

    def create_return_track(self):
        self.return_tracks.append(MockTrack("New Return"))

    def delete_track(self, index):
        del self.tracks[index]

    def duplicate_track(self, index):
        t = MockTrack(self.tracks[index].name + " Copy")
        self.tracks.insert(index + 1, t)

    def create_scene(self, index):
        self.scenes.insert(index, MockScene("New Scene"))

    def delete_scene(self, index):
        del self.scenes[index]

    def duplicate_scene(self, index):
        s = MockScene(self.scenes[index].name + " Copy")
        self.scenes.insert(index + 1, s)

    def jump_to_next_cue(self):
        pass

    def jump_to_prev_cue(self):
        pass


class MockBrowserItem:
    """Simulates a Live BrowserItem."""

    def __init__(self, name, uri=None, is_loadable=False, children=None):
        self.name = name
        self.uri = uri or ("query:" + name)
        self.is_loadable = is_loadable
        self.is_device = is_loadable
        self.children = children or []


class MockBrowser:
    """Simulates the Live Browser."""

    def __init__(self):
        synth = MockBrowserItem("Analog", "query:Analog", is_loadable=True)
        self.instruments = MockBrowserItem("Instruments", children=[synth])
        self.sounds = MockBrowserItem("Sounds")
        self.drums = MockBrowserItem("Drums")
        self.audio_effects = MockBrowserItem("Audio Effects")
        self.midi_effects = MockBrowserItem("MIDI Effects")
        self._loaded = []

    def load_item(self, item):
        self._loaded.append(item)


class MockApplication:
    """Simulates Live Application."""

    class View:
        Session = 0
        Arranger = 1

    def __init__(self):
        self.browser = MockBrowser()
        self.view = MagicMock()


class MockCInstance:
    """Simulates the c_instance passed to Remote Scripts."""

    def __init__(self, song=None):
        self._song = song or MockSong()
        self._app = MockApplication()
        self._log = []
        self._messages = []

    def song(self):
        return self._song

    def application(self):
        return self._app

    def log_message(self, msg):
        self._log.append(msg)

    def show_message(self, msg):
        self._messages.append(msg)
