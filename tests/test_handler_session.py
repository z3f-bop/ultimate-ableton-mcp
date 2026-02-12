"""Tests for the Remote Script session handler."""

import pytest

from mocks import MockSong, MockCInstance

import sys
import os

# Add remote_script to path for handler imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "..", "remote_script"))

from UltimateAbletonMCP.handlers.session import SessionHandler


@pytest.fixture
def handler(mock_song, mock_c_instance):
    return SessionHandler(mock_song, mock_c_instance)


class TestGetState:
    def test_returns_all_fields(self, handler, mock_song):
        result = handler._get_state({})
        assert result["tempo"] == 120.0
        assert result["signature_numerator"] == 4
        assert result["signature_denominator"] == 4
        assert result["time_signature"] == "4/4"
        assert result["is_playing"] is False
        assert result["record_mode"] is False
        assert result["metronome"] is False
        assert result["track_count"] == 2
        assert result["return_track_count"] == 1
        assert result["scene_count"] == 2

    def test_tracks_are_listed(self, handler):
        result = handler._get_state({})
        assert len(result["tracks"]) == 2
        assert result["tracks"][0]["name"] == "Track 1"
        assert result["tracks"][0]["type"] == "midi"
        assert result["tracks"][1]["type"] == "audio"

    def test_return_tracks_listed(self, handler):
        result = handler._get_state({})
        assert len(result["return_tracks"]) == 1

    def test_scenes_listed(self, handler):
        result = handler._get_state({})
        assert len(result["scenes"]) == 2
        assert result["scenes"][0]["name"] == "Scene 1"


class TestSetTempo:
    def test_valid_tempo(self, handler, mock_song):
        result = handler._set_tempo({"bpm": 140})
        assert mock_song.tempo == 140.0
        assert result["tempo"] == 140.0

    def test_min_tempo(self, handler, mock_song):
        result = handler._set_tempo({"bpm": 20})
        assert mock_song.tempo == 20.0

    def test_max_tempo(self, handler, mock_song):
        result = handler._set_tempo({"bpm": 999})
        assert mock_song.tempo == 999.0

    def test_below_min_raises(self, handler):
        with pytest.raises(ValueError, match="BPM must be between"):
            handler._set_tempo({"bpm": 10})

    def test_above_max_raises(self, handler):
        with pytest.raises(ValueError, match="BPM must be between"):
            handler._set_tempo({"bpm": 1000})

    def test_default_bpm(self, handler, mock_song):
        result = handler._set_tempo({})
        assert mock_song.tempo == 120.0


class TestSetTimeSignature:
    def test_valid(self, handler, mock_song):
        result = handler._set_time_signature({"numerator": 3, "denominator": 8})
        assert mock_song.signature_numerator == 3
        assert mock_song.signature_denominator == 8
        assert result["numerator"] == 3
        assert result["denominator"] == 8

    def test_invalid_numerator(self, handler):
        with pytest.raises(ValueError, match="Numerator"):
            handler._set_time_signature({"numerator": 0, "denominator": 4})

    def test_invalid_denominator(self, handler):
        with pytest.raises(ValueError, match="Denominator"):
            handler._set_time_signature({"numerator": 4, "denominator": 3})

    def test_all_valid_denominators(self, handler, mock_song):
        for denom in (1, 2, 4, 8, 16):
            handler._set_time_signature({"numerator": 4, "denominator": denom})
            assert mock_song.signature_denominator == denom


class TestSetLoop:
    def test_set_loop(self, handler, mock_song):
        result = handler._set_loop({"start": 8.0, "length": 16.0})
        assert mock_song.loop_start == 8.0
        assert mock_song.loop_length == 16.0
        assert result["loop_start"] == 8.0
        assert result["loop_length"] == 16.0


class TestSetMetronome:
    def test_enable(self, handler, mock_song):
        result = handler._set_metronome({"enabled": True})
        assert mock_song.metronome is True
        assert result["metronome"] is True

    def test_disable(self, handler, mock_song):
        mock_song.metronome = True
        result = handler._set_metronome({"enabled": False})
        assert mock_song.metronome is False


class TestUndoRedo:
    def test_undo(self, handler):
        result = handler._undo({})
        assert "Undo" in result["message"]

    def test_redo(self, handler):
        result = handler._redo({})
        assert "Redo" in result["message"]


class TestAutomation:
    def test_arrangement_overdub(self, handler, mock_song):
        result = handler._set_arrangement_overdub({"enabled": True})
        assert mock_song.arrangement_overdub is True

    def test_session_automation_record(self, handler, mock_song):
        result = handler._set_session_automation_record({"enabled": True})
        assert mock_song.session_automation_record is True

    def test_re_enable_automation(self, handler):
        result = handler._re_enable_automation({})
        assert "re-enabled" in result["message"].lower()


class TestActionRegistration:
    def test_all_actions_registered(self, handler):
        actions = handler.get_actions()
        expected = [
            "get_session_state", "set_tempo", "set_time_signature",
            "set_loop", "set_metronome", "tap_tempo", "undo", "redo",
            "set_arrangement_overdub", "set_session_automation_record",
            "re_enable_automation",
        ]
        for action in expected:
            assert action in actions, f"Missing action: {action}"
            assert callable(actions[action])

    def test_no_duplicate_actions(self, handler):
        actions = handler.get_actions()
        # dict keys are unique by definition, but let's verify count matches
        assert len(actions) == 11
