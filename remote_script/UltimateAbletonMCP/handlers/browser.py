"""Browser handler — content browser and groove pool."""


class BrowserHandler(object):

    def __init__(self, song, c_instance):
        self._song = song
        self._c = c_instance

    def get_actions(self):
        return {
            "get_browser_tree": self._get_tree,
            "get_browser_items": self._get_items,
            "load_browser_item": self._load_item,
            "get_grooves": self._get_grooves,
        }

    def _get_browser(self):
        app = self._c.application()
        if not app or not hasattr(app, "browser"):
            raise RuntimeError("Browser not available")
        return app.browser

    def _get_tree(self, params):
        browser = self._get_browser()
        category = params.get("category", "all")

        category_map = {
            "instruments": "instruments",
            "sounds": "sounds",
            "drums": "drums",
            "audio_effects": "audio_effects",
            "midi_effects": "midi_effects",
        }

        categories = []
        if category == "all":
            targets = list(category_map.keys())
        else:
            targets = [category] if category in category_map else []

        for cat_name in targets:
            attr = category_map.get(cat_name)
            if attr and hasattr(browser, attr):
                root = getattr(browser, attr)
                children = self._get_children(root, max_depth=2)
                categories.append({
                    "name": cat_name,
                    "children": children,
                })

        return {"categories": categories}

    def _get_children(self, item, depth=0, max_depth=2):
        children = []
        if not hasattr(item, "children") or depth >= max_depth:
            return children
        for child in item.children:
            info = {
                "name": child.name if hasattr(child, "name") else "Unknown",
                "uri": child.uri if hasattr(child, "uri") else None,
                "is_folder": hasattr(child, "children") and bool(child.children),
                "is_loadable": hasattr(child, "is_loadable") and child.is_loadable,
            }
            if info["is_folder"] and depth + 1 < max_depth:
                info["children"] = self._get_children(child, depth + 1, max_depth)
            children.append(info)
        return children

    def _get_items(self, params):
        browser = self._get_browser()
        path = params.get("path", "")
        parts = path.split("/")
        if not parts:
            raise ValueError("Empty path")

        # Navigate to root category
        root_name = parts[0].lower()
        category_map = {
            "instruments": "instruments",
            "sounds": "sounds",
            "drums": "drums",
            "audio_effects": "audio_effects",
            "midi_effects": "midi_effects",
        }
        attr = category_map.get(root_name)
        if not attr or not hasattr(browser, attr):
            return {"error": "Unknown category: %s" % root_name,
                    "available": list(category_map.keys())}

        current = getattr(browser, attr)

        # Navigate through remaining path parts
        for part in parts[1:]:
            if not part:
                continue
            if not hasattr(current, "children"):
                return {"error": "No children at path part: %s" % part}
            found = False
            for child in current.children:
                if hasattr(child, "name") and child.name.lower() == part.lower():
                    current = child
                    found = True
                    break
            if not found:
                return {"error": "Path part '%s' not found" % part}

        # Return items at current path
        items = []
        if hasattr(current, "children"):
            for child in current.children:
                items.append({
                    "name": child.name if hasattr(child, "name") else "Unknown",
                    "uri": child.uri if hasattr(child, "uri") else None,
                    "is_folder": hasattr(child, "children") and bool(child.children),
                    "is_loadable": hasattr(child, "is_loadable") and child.is_loadable,
                })
        return {"path": path, "items": items, "count": len(items)}

    def _load_item(self, params):
        browser = self._get_browser()
        ti = int(params.get("track_index", 0))
        uri = params.get("uri", "")

        if not uri:
            raise ValueError("URI required")

        tracks = self._song.tracks
        if ti < 0 or ti >= len(tracks):
            raise IndexError("Track index out of range")

        track = tracks[ti]

        # Find the browser item by URI
        item = self._find_by_uri(browser, uri)
        if not item:
            raise ValueError("Browser item not found: %s" % uri)

        # Select track and load
        self._song.view.selected_track = track
        browser.load_item(item)

        return {"loaded": True, "item_name": item.name, "track_index": ti}

    def _find_by_uri(self, browser, uri, max_depth=10):
        """Recursively find a browser item by URI."""
        categories = []
        for attr in ("instruments", "sounds", "drums", "audio_effects", "midi_effects"):
            if hasattr(browser, attr):
                categories.append(getattr(browser, attr))

        for cat in categories:
            result = self._search_item(cat, uri, 0, max_depth)
            if result:
                return result
        return None

    def _search_item(self, item, uri, depth, max_depth):
        if depth >= max_depth:
            return None
        if hasattr(item, "uri") and item.uri == uri:
            return item
        if hasattr(item, "children"):
            for child in item.children:
                result = self._search_item(child, uri, depth + 1, max_depth)
                if result:
                    return result
        return None

    def _get_grooves(self, params):
        pool = self._song.groove_pool
        grooves = []
        if hasattr(pool, "grooves"):
            for i, g in enumerate(pool.grooves):
                grooves.append({
                    "index": i,
                    "name": g.name if hasattr(g, "name") else "Groove %d" % i,
                })
        return {"grooves": grooves, "count": len(grooves)}
