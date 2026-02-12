# ultimate-ableton-mcp

MCP server for Ableton Live with 7 operation-dispatched tools.

## Architecture

**MCP Server** (Python, runs on host):
- `src/ultimate_ableton_mcp/server.py` — FastMCP entry, 7 tools
- `src/ultimate_ableton_mcp/connection.py` — TCP client, newline-delimited JSON
- `src/ultimate_ableton_mcp/tools/` — One file per tool (session, transport, track, clip, device, scene, browser)

**Remote Script** (Python, runs inside Ableton Live):
- `remote_script/UltimateAbletonMCP/__init__.py` — Socket server + queue + dispatch
- `remote_script/UltimateAbletonMCP/handlers/` — One handler per domain

## Protocol

Newline-delimited JSON over TCP (port 9877, configurable via `ABLETON_MCP_PORT`).

Request: `{"id": "req_42", "action": "set_track_volume", "params": {"track_index": 0, "value": 0.75}}\n`
Response: `{"id": "req_42", "ok": true, "result": {...}}\n`

## Tools

1. `ableton_session` — Tempo, time sig, loop, metronome, undo/redo
2. `ableton_transport` — Play, stop, record, seek, views
3. `ableton_track` — CRUD, volume/pan/mute/solo/arm, sends, routing, freeze/flatten
4. `ableton_clip` — Create, fire, stop, MIDI notes, loops, arrangement
5. `ableton_device` — Params, presets, automation, rack chains
6. `ableton_scene` — Create, fire, rename, color, tempo
7. `ableton_browser` — Browse instruments/effects, load items, grooves
