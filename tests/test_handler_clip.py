"""Tests for the Remote Script clip handler."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "remote_script"))

from UltimateAbletonMCP.handlers.clip import ClipHandler
from mocks import MockSong, MockCInstance, MockClip, MockClipSlot


@pytest.fixture
def handler(mock_song, mock_c_instance):
    return ClipHandler(mock_song, mock_c_instance)


@pytest.fixture
def song_with_clip(mock_song):
    """Song with a clip in track 0, scene 0."""
    clip = MockClip("Test Clip", length=4.0)
    mock_song.tracks[0].clip_slots[0] = MockClipSlot(has_clip=True, clip=clip)
    return mock_song


class TestCreateClip:
    def test_create(self, handler, mock_song):
        result = handler._create(
            {"track_index": 0, "scene_index": 0, "length": 8.0})
        assert result["length"] == 8.0
        assert mock_song.tracks[0].clip_slots[0].has_clip is True

    def test_create_default_length(self, handler, mock_song):
        result = handler._create({"track_index": 0, "scene_index": 0})
        assert result["length"] == 4.0

    def test_create_on_occupied_slot_raises(self, handler, song_with_clip):
        with pytest.raises(RuntimeError, match="already has a clip"):
            handler._create({"track_index": 0, "scene_index": 0})

    def test_track_out_of_range(self, handler):
        with pytest.raises(IndexError):
            handler._create({"track_index": 99, "scene_index": 0})

    def test_scene_out_of_range(self, handler):
        with pytest.raises(IndexError):
            handler._create({"track_index": 0, "scene_index": 99})


class TestDeleteClip:
    def test_delete(self, handler, song_with_clip):
        result = handler._delete({"track_index": 0, "scene_index": 0})
        assert result["deleted"] is True
        assert song_with_clip.tracks[0].clip_slots[0].has_clip is False

    def test_delete_empty_slot_raises(self, handler, mock_song):
        with pytest.raises(RuntimeError, match="No clip"):
            handler._delete({"track_index": 0, "scene_index": 0})


class TestFireAndStop:
    def test_fire(self, handler, song_with_clip):
        result = handler._fire({"track_index": 0, "scene_index": 0})
        assert result["fired"] is True
        assert song_with_clip.tracks[0].clip_slots[0]._fired is True

    def test_stop(self, handler, song_with_clip):
        result = handler._stop({"track_index": 0, "scene_index": 0})
        assert result["stopped"] is True


class TestGetClip:
    def test_get_with_clip(self, handler, song_with_clip):
        result = handler._get({"track_index": 0, "scene_index": 0})
        assert result["has_clip"] is True
        assert result["name"] == "Test Clip"
        assert result["length"] == 4.0
        assert "loop_start" in result
        assert "loop_end" in result

    def test_get_empty_slot(self, handler, mock_song):
        result = handler._get({"track_index": 0, "scene_index": 0})
        assert result["has_clip"] is False


class TestRenameClip:
    def test_rename(self, handler, song_with_clip):
        result = handler._rename(
            {"track_index": 0, "scene_index": 0, "name": "Bassline"})
        assert result["name"] == "Bassline"

    def test_rename_empty_slot_raises(self, handler, mock_song):
        with pytest.raises(RuntimeError, match="No clip"):
            handler._rename(
                {"track_index": 0, "scene_index": 0, "name": "X"})


class TestSetLoop:
    def test_set_loop(self, handler, song_with_clip):
        result = handler._set_loop(
            {"track_index": 0, "scene_index": 0, "start": 1.0, "end": 3.0})
        clip = song_with_clip.tracks[0].clip_slots[0].clip
        assert clip.loop_start == 1.0
        assert clip.loop_end == 3.0
        assert result["loop_start"] == 1.0
        assert result["loop_end"] == 3.0


class TestMidiNotes:
    def test_add_notes(self, handler, song_with_clip):
        notes = [
            {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100},
            {"pitch": 64, "start": 1.0, "duration": 0.5, "velocity": 80},
        ]
        result = handler._add_notes(
            {"track_index": 0, "scene_index": 0, "notes": notes})
        assert result["added"] == 2

    def test_get_notes_after_add(self, handler, song_with_clip):
        handler._add_notes({"track_index": 0, "scene_index": 0, "notes": [
            {"pitch": 60, "start": 0, "duration": 1, "velocity": 100},
        ]})
        result = handler._get_notes({"track_index": 0, "scene_index": 0})
        assert result["count"] == 1
        assert result["notes"][0]["pitch"] == 60

    def test_remove_notes(self, handler, song_with_clip):
        handler._add_notes({"track_index": 0, "scene_index": 0, "notes": [
            {"pitch": 60, "start": 0, "duration": 1, "velocity": 100},
        ]})
        result = handler._remove_notes({"track_index": 0, "scene_index": 0})
        assert result["removed"] is True

    def test_set_notes_replaces(self, handler, song_with_clip):
        # Add initial notes
        handler._add_notes({"track_index": 0, "scene_index": 0, "notes": [
            {"pitch": 60, "start": 0, "duration": 1, "velocity": 100},
        ]})
        # Replace with new notes
        new_notes = [
            {"pitch": 72, "start": 0, "duration": 2, "velocity": 64},
            {"pitch": 76, "start": 2, "duration": 2, "velocity": 64},
        ]
        result = handler._set_notes(
            {"track_index": 0, "scene_index": 0, "notes": new_notes})
        assert result["set"] == 2

    def test_note_defaults(self, handler, song_with_clip):
        """Notes with minimal params should use sensible defaults."""
        handler._add_notes({"track_index": 0, "scene_index": 0, "notes": [
            {},  # all defaults
        ]})
        result = handler._get_notes({"track_index": 0, "scene_index": 0})
        note = result["notes"][0]
        assert note["pitch"] == 60  # default
        assert note["velocity"] == 100  # default

    def test_add_notes_empty_slot_raises(self, handler, mock_song):
        with pytest.raises(RuntimeError, match="No clip"):
            handler._add_notes(
                {"track_index": 0, "scene_index": 0, "notes": []})


class TestStopAll:
    def test_stop_all(self, handler, mock_song):
        result = handler._stop_all({})
        assert result["stopped_all"] is True


class TestActionRegistration:
    def test_all_actions(self, handler):
        actions = handler.get_actions()
        expected = [
            "create_clip", "delete_clip", "duplicate_clip",
            "fire_clip", "stop_clip", "get_clip", "rename_clip",
            "set_clip_loop", "add_clip_notes", "get_clip_notes",
            "remove_clip_notes", "set_clip_notes",
            "get_arrangement_clips", "duplicate_clip_to_arrangement",
            "set_clip_groove", "stop_all_clips",
        ]
        for action in expected:
            assert action in actions, f"Missing: {action}"
        assert len(actions) == 16
