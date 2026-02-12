"""Tests for MCP tool dispatch — verifies each tool routes operations
to the correct connection.send() calls with proper parameters."""

import json
from unittest.mock import MagicMock, patch

import pytest

# We need to mock connection before importing tools
_mock_conn = MagicMock()


def _mock_get_connection():
    return _mock_conn


# Patch at module level before tool imports
@pytest.fixture(autouse=True)
def reset_mock():
    """Reset the mock connection before each test."""
    _mock_conn.reset_mock()
    _mock_conn.send.return_value = {}


@pytest.fixture(autouse=True)
def patch_connection():
    """Patch get_connection for all tool tests."""
    with patch("ultimate_ableton_mcp.tools.session.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.transport.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.track.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.clip.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.device.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.scene.get_connection", _mock_get_connection), \
         patch("ultimate_ableton_mcp.tools.browser.get_connection", _mock_get_connection):
        yield


# Import the actual tool functions (they are registered on mcp but also callable directly)
from ultimate_ableton_mcp.tools.session import ableton_session
from ultimate_ableton_mcp.tools.transport import ableton_transport
from ultimate_ableton_mcp.tools.track import ableton_track
from ultimate_ableton_mcp.tools.clip import ableton_clip
from ultimate_ableton_mcp.tools.device import ableton_device
from ultimate_ableton_mcp.tools.scene import ableton_scene
from ultimate_ableton_mcp.tools.browser import ableton_browser


class TestSessionDispatch:
    """Test ableton_session routes to correct actions."""

    def test_get_state(self):
        _mock_conn.send.return_value = {"tempo": 120}
        result = ableton_session("get_state")
        _mock_conn.send.assert_called_once_with("get_session_state")
        assert json.loads(result)["tempo"] == 120

    def test_set_tempo(self):
        ableton_session("set_tempo", bpm=140.0)
        _mock_conn.send.assert_called_once_with("set_tempo", {"bpm": 140.0})

    def test_set_time_signature(self):
        ableton_session("set_time_signature", numerator=3, denominator=8)
        _mock_conn.send.assert_called_once_with(
            "set_time_signature", {"numerator": 3, "denominator": 8})

    def test_set_loop(self):
        ableton_session("set_loop", start=4.0, length=8.0)
        _mock_conn.send.assert_called_once_with(
            "set_loop", {"start": 4.0, "length": 8.0})

    def test_set_metronome(self):
        ableton_session("set_metronome", enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_metronome", {"enabled": True})

    def test_tap_tempo(self):
        ableton_session("tap_tempo")
        _mock_conn.send.assert_called_once_with("tap_tempo")

    def test_undo(self):
        ableton_session("undo")
        _mock_conn.send.assert_called_once_with("undo")

    def test_redo(self):
        ableton_session("redo")
        _mock_conn.send.assert_called_once_with("redo")

    def test_set_arrangement_overdub(self):
        ableton_session("set_arrangement_overdub", enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_arrangement_overdub", {"enabled": True})

    def test_set_session_automation_record(self):
        ableton_session("set_session_automation_record", enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_session_automation_record", {"enabled": True})

    def test_re_enable_automation(self):
        ableton_session("re_enable_automation")
        _mock_conn.send.assert_called_once_with("re_enable_automation")

    def test_unknown_operation(self):
        result = ableton_session("nonexistent")
        assert "Unknown operation" in result
        _mock_conn.send.assert_not_called()


class TestTransportDispatch:
    """Test ableton_transport routes to correct actions."""

    def test_play(self):
        ableton_transport("play")
        _mock_conn.send.assert_called_once_with("start_playback")

    def test_stop(self):
        ableton_transport("stop")
        _mock_conn.send.assert_called_once_with("stop_playback")

    def test_continue(self):
        ableton_transport("continue")
        _mock_conn.send.assert_called_once_with("continue_playback")

    def test_record(self):
        ableton_transport("record", enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_record", {"enabled": True})

    def test_seek(self):
        ableton_transport("seek", time=16.0)
        _mock_conn.send.assert_called_once_with("seek", {"time": 16.0})

    def test_jump_to_cue_next(self):
        ableton_transport("jump_to_cue", direction="next")
        _mock_conn.send.assert_called_once_with(
            "jump_to_cue", {"direction": "next"})

    def test_jump_to_cue_prev(self):
        ableton_transport("jump_to_cue", direction="prev")
        _mock_conn.send.assert_called_once_with(
            "jump_to_cue", {"direction": "prev"})

    def test_scroll_to_time(self):
        ableton_transport("scroll_to_time", time=32.0)
        _mock_conn.send.assert_called_once_with(
            "scroll_to_time", {"time": 32.0})

    def test_show_view(self):
        ableton_transport("show_view", view="arrangement")
        _mock_conn.send.assert_called_once_with(
            "show_view", {"view": "arrangement"})

    def test_unknown_operation(self):
        result = ableton_transport("warp")
        assert "Unknown operation" in result


class TestTrackDispatch:
    """Test ableton_track routes to correct actions."""

    def test_list(self):
        ableton_track("list")
        _mock_conn.send.assert_called_once_with("list_tracks")

    def test_get(self):
        ableton_track("get", track_index=2)
        _mock_conn.send.assert_called_once_with(
            "get_track", {"track_index": 2})

    def test_create_midi(self):
        ableton_track("create", type="midi", name="Bass", index=0)
        _mock_conn.send.assert_called_once_with(
            "create_track", {"type": "midi", "name": "Bass", "index": 0})

    def test_create_audio(self):
        ableton_track("create", type="audio")
        _mock_conn.send.assert_called_once_with(
            "create_track", {"type": "audio", "name": "", "index": -1})

    def test_delete(self):
        ableton_track("delete", track_index=3)
        _mock_conn.send.assert_called_once_with(
            "delete_track", {"track_index": 3})

    def test_duplicate(self):
        ableton_track("duplicate", track_index=1)
        _mock_conn.send.assert_called_once_with(
            "duplicate_track", {"track_index": 1})

    def test_rename(self):
        ableton_track("rename", track_index=0, name="Lead Synth")
        _mock_conn.send.assert_called_once_with(
            "rename_track", {"track_index": 0, "name": "Lead Synth"})

    def test_set_volume(self):
        ableton_track("set_volume", track_index=0, value=0.75)
        _mock_conn.send.assert_called_once_with(
            "set_track_volume", {"track_index": 0, "value": 0.75})

    def test_set_pan(self):
        ableton_track("set_pan", track_index=0, value=-0.5)
        _mock_conn.send.assert_called_once_with(
            "set_track_pan", {"track_index": 0, "value": -0.5})

    def test_set_mute(self):
        ableton_track("set_mute", track_index=0, enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_track_mute", {"track_index": 0, "enabled": True})

    def test_set_solo(self):
        ableton_track("set_solo", track_index=0, enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_track_solo", {"track_index": 0, "enabled": True})

    def test_set_arm(self):
        ableton_track("set_arm", track_index=0, enabled=True)
        _mock_conn.send.assert_called_once_with(
            "set_track_arm", {"track_index": 0, "enabled": True})

    def test_set_color(self):
        ableton_track("set_color", track_index=0, color=42)
        _mock_conn.send.assert_called_once_with(
            "set_track_color", {"track_index": 0, "color": 42})

    def test_set_send(self):
        ableton_track("set_send", track_index=0, send_index=1, value=0.6)
        _mock_conn.send.assert_called_once_with(
            "set_track_send",
            {"track_index": 0, "send_index": 1, "value": 0.6})

    def test_set_input_routing(self):
        ableton_track("set_input_routing", track_index=0,
                      routing_type="All Ins", channel="1/2")
        _mock_conn.send.assert_called_once_with(
            "set_track_input_routing",
            {"track_index": 0, "routing_type": "All Ins", "channel": "1/2"})

    def test_set_output_routing(self):
        ableton_track("set_output_routing", track_index=0,
                      routing_type="Sends Only")
        _mock_conn.send.assert_called_once_with(
            "set_track_output_routing",
            {"track_index": 0, "routing_type": "Sends Only", "channel": ""})

    def test_freeze(self):
        ableton_track("freeze", track_index=0)
        _mock_conn.send.assert_called_once_with(
            "freeze_track", {"track_index": 0})

    def test_flatten(self):
        ableton_track("flatten", track_index=0)
        _mock_conn.send.assert_called_once_with(
            "flatten_track", {"track_index": 0})

    def test_stop_all_clips(self):
        ableton_track("stop_all_clips", track_index=0)
        _mock_conn.send.assert_called_once_with(
            "stop_track_clips", {"track_index": 0})

    def test_unknown_operation(self):
        result = ableton_track("warp")
        assert "Unknown operation" in result


class TestClipDispatch:
    """Test ableton_clip routes to correct actions."""

    def test_create(self):
        ableton_clip("create", track_index=0, scene_index=0, length=8.0)
        _mock_conn.send.assert_called_once_with(
            "create_clip",
            {"track_index": 0, "scene_index": 0, "length": 8.0})

    def test_delete(self):
        ableton_clip("delete", track_index=0, scene_index=1)
        _mock_conn.send.assert_called_once_with(
            "delete_clip", {"track_index": 0, "scene_index": 1})

    def test_fire(self):
        ableton_clip("fire", track_index=0, scene_index=0)
        _mock_conn.send.assert_called_once_with(
            "fire_clip", {"track_index": 0, "scene_index": 0})

    def test_add_notes(self):
        notes = [{"pitch": 60, "start": 0, "duration": 1, "velocity": 100}]
        ableton_clip("add_notes", track_index=0, scene_index=0, notes=notes)
        _mock_conn.send.assert_called_once_with(
            "add_clip_notes",
            {"track_index": 0, "scene_index": 0, "notes": notes})

    def test_get_notes(self):
        ableton_clip("get_notes", track_index=0, scene_index=0)
        _mock_conn.send.assert_called_once_with(
            "get_clip_notes", {"track_index": 0, "scene_index": 0})

    def test_set_notes(self):
        notes = [{"pitch": 64, "start": 0, "duration": 2, "velocity": 80}]
        ableton_clip("set_notes", track_index=0, scene_index=0, notes=notes)
        _mock_conn.send.assert_called_once_with(
            "set_clip_notes",
            {"track_index": 0, "scene_index": 0, "notes": notes})

    def test_set_loop(self):
        ableton_clip("set_loop", track_index=0, scene_index=0,
                     start=2.0, end=6.0)
        _mock_conn.send.assert_called_once_with(
            "set_clip_loop",
            {"track_index": 0, "scene_index": 0, "start": 2.0, "end": 6.0})

    def test_stop_all(self):
        ableton_clip("stop_all")
        _mock_conn.send.assert_called_once_with("stop_all_clips")

    def test_get_arrangement_clips(self):
        ableton_clip("get_arrangement_clips", track_index=1)
        _mock_conn.send.assert_called_once_with(
            "get_arrangement_clips", {"track_index": 1})

    def test_unknown_operation(self):
        result = ableton_clip("quantize")
        assert "Unknown operation" in result


class TestDeviceDispatch:
    """Test ableton_device routes to correct actions."""

    def test_list(self):
        ableton_device("list", track_index=0)
        _mock_conn.send.assert_called_once_with(
            "list_devices", {"track_index": 0})

    def test_get(self):
        ableton_device("get", track_index=0, device_index=1)
        _mock_conn.send.assert_called_once_with(
            "get_device", {"track_index": 0, "device_index": 1})

    def test_get_param_by_index(self):
        ableton_device("get_param", track_index=0, device_index=0, param=2)
        _mock_conn.send.assert_called_once_with(
            "get_device_param",
            {"track_index": 0, "device_index": 0, "param": 2})

    def test_set_param(self):
        ableton_device("set_param", track_index=0, device_index=0,
                       param="Filter Freq", value=5000.0)
        _mock_conn.send.assert_called_once_with(
            "set_device_param",
            {"track_index": 0, "device_index": 0,
             "param": "Filter Freq", "value": 5000.0})

    def test_set_enabled(self):
        ableton_device("set_enabled", track_index=0, device_index=0,
                       enabled=False)
        _mock_conn.send.assert_called_once_with(
            "set_device_enabled",
            {"track_index": 0, "device_index": 0, "enabled": False})

    def test_get_chains(self):
        ableton_device("get_chains", track_index=0, device_index=0)
        _mock_conn.send.assert_called_once_with(
            "get_device_chains",
            {"track_index": 0, "device_index": 0})

    def test_insert_automation_point(self):
        ableton_device("insert_automation_point", track_index=0,
                       clip_index=0, device_index=0, param_index=1,
                       time=2.0, value=0.5)
        _mock_conn.send.assert_called_once_with(
            "insert_automation_point",
            {"track_index": 0, "device_index": 0, "clip_index": 0,
             "param_index": 1, "time": 2.0, "value": 0.5})

    def test_unknown_operation(self):
        result = ableton_device("morph")
        assert "Unknown operation" in result


class TestSceneDispatch:
    """Test ableton_scene routes to correct actions."""

    def test_list(self):
        ableton_scene("list")
        _mock_conn.send.assert_called_once_with("list_scenes")

    def test_create(self):
        ableton_scene("create", name="Drop")
        _mock_conn.send.assert_called_once_with(
            "create_scene", {"name": "Drop"})

    def test_fire(self):
        ableton_scene("fire", scene_index=2)
        _mock_conn.send.assert_called_once_with(
            "fire_scene", {"scene_index": 2})

    def test_rename(self):
        ableton_scene("rename", scene_index=0, name="Intro")
        _mock_conn.send.assert_called_once_with(
            "rename_scene", {"scene_index": 0, "name": "Intro"})

    def test_set_tempo(self):
        ableton_scene("set_tempo", scene_index=0, bpm=128.0)
        _mock_conn.send.assert_called_once_with(
            "set_scene_tempo", {"scene_index": 0, "bpm": 128.0})

    def test_unknown_operation(self):
        result = ableton_scene("shuffle")
        assert "Unknown operation" in result


class TestBrowserDispatch:
    """Test ableton_browser routes to correct actions."""

    def test_get_tree(self):
        ableton_browser("get_tree", category="instruments")
        _mock_conn.send.assert_called_once_with(
            "get_browser_tree", {"category": "instruments"})

    def test_get_items(self):
        ableton_browser("get_items", path="instruments/Analog")
        _mock_conn.send.assert_called_once_with(
            "get_browser_items", {"path": "instruments/Analog"})

    def test_load_item(self):
        ableton_browser("load_item", track_index=0, uri="query:Analog")
        _mock_conn.send.assert_called_once_with(
            "load_browser_item",
            {"track_index": 0, "uri": "query:Analog"})

    def test_get_grooves(self):
        ableton_browser("get_grooves")
        _mock_conn.send.assert_called_once_with("get_grooves")

    def test_unknown_operation(self):
        result = ableton_browser("preview")
        assert "Unknown operation" in result


class TestToolReturnFormat:
    """All tools must return JSON strings or error messages."""

    def test_session_returns_valid_json(self):
        _mock_conn.send.return_value = {"tempo": 120}
        result = ableton_session("get_state")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_transport_returns_valid_json(self):
        _mock_conn.send.return_value = {"is_playing": True}
        result = ableton_transport("play")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_track_list_returns_indented_json(self):
        _mock_conn.send.return_value = {"tracks": []}
        result = ableton_track("list")
        assert "\n" in result  # indented output
        parsed = json.loads(result)
        assert "tracks" in parsed
