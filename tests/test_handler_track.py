"""Tests for the Remote Script track handler."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "remote_script"))

from UltimateAbletonMCP.handlers.track import TrackHandler
from mocks import MockSong, MockCInstance


@pytest.fixture
def handler(mock_song, mock_c_instance):
    return TrackHandler(mock_song, mock_c_instance)


class TestListTracks:
    def test_returns_all_tracks(self, handler, mock_song):
        result = handler._list({})
        assert result["count"] == 2
        assert len(result["tracks"]) == 2

    def test_track_fields(self, handler):
        result = handler._list({})
        track = result["tracks"][0]
        assert "index" in track
        assert "name" in track
        assert "type" in track
        assert "armed" in track
        assert "muted" in track
        assert "soloed" in track
        assert "volume" in track


class TestGetTrack:
    def test_valid_index(self, handler):
        result = handler._get({"track_index": 0})
        assert result["name"] == "Track 1"
        assert result["index"] == 0

    def test_includes_devices(self, handler):
        result = handler._get({"track_index": 0})
        assert "devices" in result
        assert len(result["devices"]) == 1

    def test_includes_clip_slots(self, handler):
        result = handler._get({"track_index": 0})
        assert "clip_slots" in result
        assert len(result["clip_slots"]) == 8

    def test_includes_sends(self, handler):
        result = handler._get({"track_index": 0})
        assert "sends" in result
        assert len(result["sends"]) == 2

    def test_out_of_range_raises(self, handler):
        with pytest.raises(IndexError):
            handler._get({"track_index": 99})

    def test_negative_index_raises(self, handler):
        with pytest.raises(IndexError):
            handler._get({"track_index": -1})


class TestCreateTrack:
    def test_create_midi(self, handler, mock_song):
        result = handler._create({"type": "midi"})
        assert result["type"] == "midi"
        assert len(mock_song.tracks) == 3

    def test_create_audio(self, handler, mock_song):
        result = handler._create({"type": "audio"})
        assert result["type"] == "audio"
        assert len(mock_song.tracks) == 3

    def test_create_return(self, handler, mock_song):
        result = handler._create({"type": "return"})
        assert result["type"] == "return"
        assert len(mock_song.return_tracks) == 2

    def test_create_with_name(self, handler, mock_song):
        result = handler._create({"type": "midi", "name": "Bass"})
        # The new track should be named "Bass"
        assert result["name"] == "Bass"

    def test_create_at_index(self, handler, mock_song):
        result = handler._create({"type": "midi", "index": 0})
        assert result["index"] == 0
        assert len(mock_song.tracks) == 3

    def test_invalid_type_raises(self, handler):
        with pytest.raises(ValueError, match="Unknown track type"):
            handler._create({"type": "group"})


class TestDeleteTrack:
    def test_delete(self, handler, mock_song):
        result = handler._delete({"track_index": 0})
        assert result["deleted"] == 0
        assert len(mock_song.tracks) == 1


class TestDuplicateTrack:
    def test_duplicate(self, handler, mock_song):
        result = handler._duplicate({"track_index": 0})
        assert result["duplicated"] == 0
        assert result["new_index"] == 1
        assert len(mock_song.tracks) == 3


class TestMixerOperations:
    def test_set_volume(self, handler, mock_song):
        result = handler._set_volume({"track_index": 0, "value": 0.5})
        assert result["volume"] == 0.5
        assert mock_song.tracks[0].mixer_device.volume.value == 0.5

    def test_volume_clamps_high(self, handler, mock_song):
        result = handler._set_volume({"track_index": 0, "value": 2.0})
        assert result["volume"] == 1.0

    def test_volume_clamps_low(self, handler, mock_song):
        result = handler._set_volume({"track_index": 0, "value": -1.0})
        assert result["volume"] == 0.0

    def test_set_pan(self, handler, mock_song):
        result = handler._set_pan({"track_index": 0, "value": -0.5})
        assert result["pan"] == -0.5

    def test_pan_clamps(self, handler, mock_song):
        result = handler._set_pan({"track_index": 0, "value": 5.0})
        assert result["pan"] == 1.0

    def test_set_mute(self, handler, mock_song):
        result = handler._set_mute({"track_index": 0, "enabled": True})
        assert result["mute"] is True
        assert mock_song.tracks[0].mute is True

    def test_set_solo(self, handler, mock_song):
        result = handler._set_solo({"track_index": 0, "enabled": True})
        assert result["solo"] is True

    def test_set_arm(self, handler, mock_song):
        result = handler._set_arm({"track_index": 0, "enabled": True})
        assert result["arm"] is True

    def test_set_color(self, handler, mock_song):
        result = handler._set_color({"track_index": 0, "color": 42})
        assert result["color"] == 42


class TestSends:
    def test_set_send(self, handler, mock_song):
        result = handler._set_send(
            {"track_index": 0, "send_index": 0, "value": 0.8})
        assert result["value"] == 0.8

    def test_send_clamps(self, handler, mock_song):
        result = handler._set_send(
            {"track_index": 0, "send_index": 0, "value": 5.0})
        assert result["value"] == 1.0

    def test_invalid_send_index(self, handler):
        with pytest.raises(IndexError, match="Send index"):
            handler._set_send(
                {"track_index": 0, "send_index": 99, "value": 0.5})


class TestRouting:
    def test_set_input_routing_found(self, handler):
        result = handler._set_input_routing(
            {"track_index": 0, "routing_type": "All Ins"})
        assert result["input_routing"] == "All Ins"

    def test_set_input_routing_not_found(self, handler):
        result = handler._set_input_routing(
            {"track_index": 0, "routing_type": "Nonexistent"})
        assert "error" in result
        assert "available" in result

    def test_set_output_routing_found(self, handler):
        result = handler._set_output_routing(
            {"track_index": 0, "routing_type": "Master"})
        assert result["output_routing"] == "Master"


class TestFreezeAndFlatten:
    def test_freeze(self, handler):
        result = handler._freeze({"track_index": 0})
        assert result["frozen"] is True

    def test_flatten(self, handler):
        result = handler._flatten({"track_index": 0})
        assert result["flattened"] is True


class TestActionRegistration:
    def test_all_actions(self, handler):
        actions = handler.get_actions()
        expected = [
            "list_tracks", "get_track", "create_track", "delete_track",
            "duplicate_track", "rename_track", "set_track_volume",
            "set_track_pan", "set_track_mute", "set_track_solo",
            "set_track_arm", "set_track_color", "set_track_send",
            "set_track_input_routing", "set_track_output_routing",
            "freeze_track", "flatten_track", "stop_track_clips",
        ]
        for action in expected:
            assert action in actions, f"Missing: {action}"
        assert len(actions) == 18
