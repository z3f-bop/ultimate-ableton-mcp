"""Tests for the Remote Script scene and browser handlers."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "remote_script"))

from UltimateAbletonMCP.handlers.scene import SceneHandler
from UltimateAbletonMCP.handlers.browser import BrowserHandler
from mocks import MockSong, MockCInstance


# ============================================================================
# Scene Handler Tests
# ============================================================================

@pytest.fixture
def scene_handler(mock_song, mock_c_instance):
    return SceneHandler(mock_song, mock_c_instance)


class TestSceneList:
    def test_list(self, scene_handler, mock_song):
        result = scene_handler._list({})
        assert result["count"] == 2
        assert result["scenes"][0]["name"] == "Scene 1"

    def test_scene_fields(self, scene_handler):
        result = scene_handler._list({})
        scene = result["scenes"][0]
        assert "index" in scene
        assert "name" in scene
        assert "color" in scene


class TestSceneGet:
    def test_get(self, scene_handler):
        result = scene_handler._get({"scene_index": 0})
        assert result["name"] == "Scene 1"
        assert "clips" in result

    def test_out_of_range(self, scene_handler):
        with pytest.raises(IndexError):
            scene_handler._get({"scene_index": 99})


class TestSceneCreate:
    def test_create(self, scene_handler, mock_song):
        result = scene_handler._create({"name": "Drop"})
        assert result["name"] == "Drop"
        assert len(mock_song.scenes) == 3

    def test_create_unnamed(self, scene_handler, mock_song):
        result = scene_handler._create({})
        assert len(mock_song.scenes) == 3


class TestSceneDelete:
    def test_delete(self, scene_handler, mock_song):
        result = scene_handler._delete({"scene_index": 0})
        assert result["deleted"] == 0
        assert len(mock_song.scenes) == 1


class TestSceneDuplicate:
    def test_duplicate(self, scene_handler, mock_song):
        result = scene_handler._duplicate({"scene_index": 0})
        assert result["duplicated"] == 0
        assert len(mock_song.scenes) == 3


class TestSceneFire:
    def test_fire(self, scene_handler, mock_song):
        result = scene_handler._fire({"scene_index": 0})
        assert result["fired"] == 0
        assert mock_song.scenes[0]._fired is True


class TestSceneRename:
    def test_rename(self, scene_handler, mock_song):
        result = scene_handler._rename(
            {"scene_index": 0, "name": "Intro"})
        assert result["name"] == "Intro"
        assert mock_song.scenes[0].name == "Intro"


class TestSceneColor:
    def test_set_color(self, scene_handler, mock_song):
        result = scene_handler._set_color(
            {"scene_index": 0, "color": 7})
        assert result["color"] == 7


class TestSceneActionRegistration:
    def test_all_actions(self, scene_handler):
        actions = scene_handler.get_actions()
        expected = [
            "list_scenes", "get_scene", "create_scene", "delete_scene",
            "duplicate_scene", "fire_scene", "rename_scene",
            "set_scene_color", "set_scene_tempo",
        ]
        for action in expected:
            assert action in actions, f"Missing: {action}"
        assert len(actions) == 9


# ============================================================================
# Browser Handler Tests
# ============================================================================

@pytest.fixture
def browser_handler(mock_song, mock_c_instance):
    return BrowserHandler(mock_song, mock_c_instance)


class TestBrowserGetTree:
    def test_get_all(self, browser_handler):
        result = browser_handler._get_tree({"category": "all"})
        assert "categories" in result
        assert len(result["categories"]) == 5  # instruments, sounds, drums, audio, midi

    def test_get_instruments(self, browser_handler):
        result = browser_handler._get_tree({"category": "instruments"})
        assert len(result["categories"]) == 1
        assert result["categories"][0]["name"] == "instruments"

    def test_get_instruments_has_children(self, browser_handler):
        result = browser_handler._get_tree({"category": "instruments"})
        children = result["categories"][0]["children"]
        assert len(children) == 1
        assert children[0]["name"] == "Analog"
        assert children[0]["is_loadable"] is True


class TestBrowserGetItems:
    def test_get_items_at_root(self, browser_handler):
        result = browser_handler._get_items({"path": "instruments"})
        assert result["count"] == 1
        assert result["items"][0]["name"] == "Analog"

    def test_invalid_category(self, browser_handler):
        result = browser_handler._get_items({"path": "nonexistent"})
        assert "error" in result

    def test_path_part_not_found(self, browser_handler):
        result = browser_handler._get_items(
            {"path": "instruments/Nonexistent"})
        assert "error" in result


class TestBrowserLoadItem:
    def test_load_valid_uri(self, browser_handler, mock_c_instance):
        result = browser_handler._load_item(
            {"track_index": 0, "uri": "query:Analog"})
        assert result["loaded"] is True
        assert result["item_name"] == "Analog"
        assert len(mock_c_instance._app.browser._loaded) == 1

    def test_load_invalid_uri(self, browser_handler):
        with pytest.raises(ValueError, match="not found"):
            browser_handler._load_item(
                {"track_index": 0, "uri": "query:Nonexistent"})

    def test_load_missing_uri(self, browser_handler):
        with pytest.raises(ValueError, match="URI required"):
            browser_handler._load_item({"track_index": 0, "uri": ""})

    def test_load_track_out_of_range(self, browser_handler):
        with pytest.raises(IndexError):
            browser_handler._load_item(
                {"track_index": 99, "uri": "query:Analog"})


class TestBrowserGrooves:
    def test_empty_groove_pool(self, browser_handler):
        result = browser_handler._get_grooves({})
        assert result["count"] == 0
        assert result["grooves"] == []


class TestBrowserActionRegistration:
    def test_all_actions(self, browser_handler):
        actions = browser_handler.get_actions()
        expected = [
            "get_browser_tree", "get_browser_items",
            "load_browser_item", "get_grooves",
        ]
        for action in expected:
            assert action in actions, f"Missing: {action}"
        assert len(actions) == 4
