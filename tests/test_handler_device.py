"""Tests for the Remote Script device handler."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "remote_script"))

from UltimateAbletonMCP.handlers.device import DeviceHandler
from mocks import (MockSong, MockCInstance, MockDevice, MockParam,
                      MockClip, MockClipSlot)


@pytest.fixture
def handler(mock_song, mock_c_instance):
    return DeviceHandler(mock_song, mock_c_instance)


@pytest.fixture
def song_with_clip(mock_song):
    """Song with a clip in track 0, slot 0 for automation tests."""
    clip = MockClip("Auto Clip", length=4.0)
    mock_song.tracks[0].clip_slots[0] = MockClipSlot(has_clip=True, clip=clip)
    return mock_song


class TestListDevices:
    def test_list(self, handler):
        result = handler._list({"track_index": 0})
        assert result["count"] == 1
        assert result["devices"][0]["name"] == "Simpler"

    def test_list_out_of_range(self, handler):
        with pytest.raises(IndexError):
            handler._list({"track_index": 99})


class TestGetDevice:
    def test_get(self, handler):
        result = handler._get({"track_index": 0, "device_index": 0})
        assert result["name"] == "Simpler"
        assert result["class_name"] == "OriginalSimpler"
        assert len(result["parameters"]) == 3
        assert result["parameters"][0]["name"] == "Device On"

    def test_device_out_of_range(self, handler):
        with pytest.raises(IndexError, match="Device index"):
            handler._get({"track_index": 0, "device_index": 5})


class TestGetParam:
    def test_by_index(self, handler):
        result = handler._get_param(
            {"track_index": 0, "device_index": 0, "param": 1})
        assert result["name"] == "Volume"

    def test_by_name(self, handler):
        result = handler._get_param(
            {"track_index": 0, "device_index": 0, "param": "Volume"})
        assert result["name"] == "Volume"

    def test_by_name_case_insensitive(self, handler):
        result = handler._get_param(
            {"track_index": 0, "device_index": 0, "param": "volume"})
        assert result["name"] == "Volume"

    def test_by_string_digit(self, handler):
        """String "1" should resolve as index 1."""
        result = handler._get_param(
            {"track_index": 0, "device_index": 0, "param": "1"})
        assert result["name"] == "Volume"

    def test_invalid_index(self, handler):
        with pytest.raises(IndexError, match="Parameter index"):
            handler._get_param(
                {"track_index": 0, "device_index": 0, "param": 99})

    def test_invalid_name(self, handler):
        with pytest.raises(ValueError, match="not found"):
            handler._get_param(
                {"track_index": 0, "device_index": 0, "param": "Nonexistent"})


class TestSetParam:
    def test_set(self, handler, mock_song):
        result = handler._set_param(
            {"track_index": 0, "device_index": 0, "param": 1, "value": 0.5})
        assert result["value"] == 0.5
        assert mock_song.tracks[0].devices[0].parameters[1].value == 0.5

    def test_clamps_to_max(self, handler, mock_song):
        result = handler._set_param(
            {"track_index": 0, "device_index": 0, "param": 1, "value": 99.0})
        assert result["value"] == 1.0  # max for Volume param

    def test_clamps_to_min(self, handler, mock_song):
        result = handler._set_param(
            {"track_index": 0, "device_index": 0, "param": 1, "value": -5.0})
        assert result["value"] == 0.0  # min for Volume param

    def test_set_by_name(self, handler, mock_song):
        result = handler._set_param(
            {"track_index": 0, "device_index": 0,
             "param": "Filter Freq", "value": 5000.0})
        assert result["value"] == 5000.0


class TestSetEnabled:
    def test_disable(self, handler, mock_song):
        handler._set_enabled(
            {"track_index": 0, "device_index": 0, "enabled": False})
        assert mock_song.tracks[0].devices[0].parameters[0].value == 0.0

    def test_enable(self, handler, mock_song):
        handler._set_enabled(
            {"track_index": 0, "device_index": 0, "enabled": True})
        assert mock_song.tracks[0].devices[0].parameters[0].value == 1.0


class TestPresets:
    def test_get_presets(self, handler):
        result = handler._get_presets(
            {"track_index": 0, "device_index": 0})
        assert len(result["presets"]) == 3
        assert result["presets"][0]["name"] == "Init"

    def test_set_preset(self, handler, mock_song):
        result = handler._set_preset(
            {"track_index": 0, "device_index": 0, "preset_index": 2})
        assert result["preset_index"] == 2


class TestChains:
    def test_not_a_rack(self, handler):
        result = handler._get_chains(
            {"track_index": 0, "device_index": 0})
        assert result["chains"] == []
        assert "error" in result


class TestAutomation:
    def test_get_automation_none(self, handler, song_with_clip):
        result = handler._get_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        assert result["has_automation"] is False

    def test_create_automation(self, handler, song_with_clip):
        result = handler._create_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        assert result["created"] is True

    def test_get_automation_after_create(self, handler, song_with_clip):
        handler._create_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        result = handler._get_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        assert result["has_automation"] is True

    def test_clear_automation(self, handler, song_with_clip):
        handler._create_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        result = handler._clear_automation(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1})
        assert result["cleared"] is True

    def test_insert_automation_point(self, handler, song_with_clip):
        result = handler._insert_automation_point(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1,
             "time": 2.0, "value": 0.5})
        assert result["inserted"] is True
        assert result["time"] == 2.0

    def test_remove_automation_no_envelope(self, handler, song_with_clip):
        result = handler._remove_automation_point(
            {"track_index": 0, "clip_index": 0,
             "device_index": 0, "param_index": 1, "time": 1.0})
        assert result["removed"] is False

    def test_no_clip_raises(self, handler, mock_song):
        with pytest.raises(RuntimeError, match="No clip"):
            handler._get_automation(
                {"track_index": 0, "clip_index": 0,
                 "device_index": 0, "param_index": 0})


class TestActionRegistration:
    def test_all_actions(self, handler):
        actions = handler.get_actions()
        expected = [
            "list_devices", "get_device", "get_device_param",
            "set_device_param", "set_device_enabled", "get_device_presets",
            "set_device_preset", "get_device_chains", "get_automation",
            "create_automation", "clear_automation",
            "insert_automation_point", "remove_automation_point",
        ]
        for action in expected:
            assert action in actions, f"Missing: {action}"
        assert len(actions) == 13
