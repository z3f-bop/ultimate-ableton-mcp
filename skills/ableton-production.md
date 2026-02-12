# Ableton Production — Session Architecture & Workflow

Domain knowledge for structuring sessions, managing tracks, and production workflow in Ableton Live 12 via MCP tools.

## Session Setup Workflow

### 1. Always start by reading the session state

```
ableton_session(operation="get_state")
```

This returns tempo, time signature, track/scene count, transport state, loop settings. **Read before you act.**

### 2. Understand the track layout before modifying

```
ableton_track(operation="list")
```

Returns all tracks with types (midi/audio), armed state, volume, mute/solo. **Never create tracks blindly — check what exists first.**

### 3. Inspect individual tracks for detail

```
ableton_track(operation="get", track_index=0)
```

Returns devices, clip slots, sends, routing. Use this to understand what's already on a track before adding to it.

## Track Organization Patterns

### Standard Session Template

| Track | Type | Purpose |
|-------|------|---------|
| 0-3 | MIDI | Drums, Bass, Lead, Pads |
| 4-5 | Audio | Samples, Vocals |
| 6 | Return A | Reverb send |
| 7 | Return B | Delay send |

### Creating a track with routing

```python
# Create MIDI track at specific position
ableton_track(operation="create", type="midi", name="Bass", index=1)

# Create return track for effects
ableton_track(operation="create", type="return")

# Route a track's send to return
ableton_track(operation="set_send", track_index=0, send_index=0, value=0.5)
```

### Color coding (Live color indices)

Use `set_color` with integer color index. Common convention:
- Drums: warm colors (reds/oranges)
- Bass: cool colors (blues)
- Melodic: greens/teals
- Effects/returns: grays/purples

## Scene-Based Arrangement

### Building a song structure with scenes

Scenes = song sections. Name them descriptively:

```python
# Create and name scenes for song structure
ableton_scene(operation="create", name="Intro")
ableton_scene(operation="create", name="Verse 1")
ableton_scene(operation="create", name="Chorus")
ableton_scene(operation="create", name="Verse 2")
ableton_scene(operation="create", name="Bridge")
ableton_scene(operation="create", name="Outro")
```

### Scene tempo changes

Some genres use tempo changes between sections:

```python
# Drop section at higher energy
ableton_scene(operation="set_tempo", scene_index=2, bpm=128)
# Breakdown at lower tempo
ableton_scene(operation="set_tempo", scene_index=4, bpm=120)
```

### Firing scenes for live performance

```python
ableton_scene(operation="fire", scene_index=0)  # Launch entire row
```

## Transport & Recording

### Recording workflow

```python
# 1. Arm the target track
ableton_track(operation="set_arm", track_index=0, enabled=True)

# 2. Set metronome for timing
ableton_session(operation="set_metronome", enabled=True)

# 3. Start recording
ableton_transport(operation="record", enabled=True)

# 4. Stop when done
ableton_transport(operation="stop")
```

### Arrangement overdub

For layering takes in arrangement view:

```python
ableton_session(operation="set_arrangement_overdub", enabled=True)
ableton_transport(operation="record", enabled=True)
```

## Tempo & Time Signature

### Standard ranges by genre

| Genre | BPM Range | Time Sig |
|-------|-----------|----------|
| Hip-Hop | 80-100 | 4/4 |
| House | 120-130 | 4/4 |
| Techno | 125-145 | 4/4 |
| Drum & Bass | 170-180 | 4/4 |
| Trap | 130-170 (half-time feel) | 4/4 |
| Ambient | 60-90 | varies |
| Breakbeat | 130-150 | 4/4 |

### Setting tempo with validation

```python
ableton_session(operation="set_tempo", bpm=128)
# Live accepts 20-999 BPM — handler validates range
```

## Mixing Basics

### Gain staging

Volume in Live is 0.0-1.0 (where 0.85 ≈ 0dB):

```python
# Set relative levels
ableton_track(operation="set_volume", track_index=0, value=0.75)  # Drums slightly back
ableton_track(operation="set_volume", track_index=1, value=0.85)  # Bass at unity
ableton_track(operation="set_volume", track_index=2, value=0.65)  # Lead tucked under
```

### Pan law

Pan is -1.0 (full left) to 1.0 (full right):

```python
ableton_track(operation="set_pan", track_index=0, value=-0.3)  # Slightly left
ableton_track(operation="set_pan", track_index=1, value=0.0)   # Center (bass always)
ableton_track(operation="set_pan", track_index=2, value=0.3)   # Slightly right
```

### Solo/mute workflow

```python
# Solo a track to hear it isolated
ableton_track(operation="set_solo", track_index=0, enabled=True)
# Mute a track to remove it from mix
ableton_track(operation="set_mute", track_index=3, enabled=True)
```

## Freeze & Flatten

For CPU-heavy tracks with lots of effects:

```python
# Freeze renders the track to audio (reversible)
ableton_track(operation="freeze", track_index=0)
# Flatten commits the freeze permanently (irreversible!)
ableton_track(operation="flatten", track_index=0)
```

**Warning:** Flatten is destructive. Always confirm with the user before flattening.

## Undo/Redo

Ableton has deep undo history:

```python
ableton_session(operation="undo")  # Ctrl+Z equivalent
ableton_session(operation="redo")  # Ctrl+Shift+Z equivalent
```

**Use undo after mistakes.** It's safer to undo and retry than to manually fix.

## Common Pitfalls

1. **Don't create clips in occupied slots** — check `get_clip` first
2. **Don't arm return tracks** — they can't be armed
3. **Don't set volume > 1.0** — it will clamp, but it's bad practice
4. **Always `get_state` first** — understand the session before modifying
5. **Name everything** — unnamed tracks/clips/scenes make sessions unnavigable
6. **Check track type before operations** — MIDI operations on audio tracks will fail
