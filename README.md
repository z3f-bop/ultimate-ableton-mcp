# ultimate-ableton-mcp

MCP server for Ableton Live — 7 operation-dispatched tools covering the full Live Object Model.

## Quick Start

```bash
# Install Remote Script
./scripts/install-remote-script.sh

# In Ableton: Preferences > Control Surface > UltimateAbletonMCP

# Run MCP server
uv run ultimate-ableton-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `ableton_session` | Tempo, time sig, loop, metronome, undo/redo |
| `ableton_transport` | Play, stop, record, seek, views |
| `ableton_track` | CRUD, mix (volume/pan/mute/solo/arm), sends, routing |
| `ableton_clip` | Clips, MIDI notes, loops, arrangement |
| `ableton_device` | Parameters, presets, automation, rack chains |
| `ableton_scene` | Scene management |
| `ableton_browser` | Browse & load instruments/effects, grooves |

## License

MIT
