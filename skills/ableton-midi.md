# Ableton MIDI — Notes, Patterns & Clip Programming

Domain knowledge for programming MIDI clips, building patterns, and manipulating notes via `ableton_clip` tool.

## Note Format

Every note is a tuple: `(pitch, start, duration, velocity, mute)`

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `pitch` | int | 0-127 | MIDI note number (60 = C4) |
| `start` | float | 0.0+ | Position in beats from clip start |
| `duration` | float | 0.0+ | Length in beats |
| `velocity` | int | 1-127 | How hard the note is hit |
| `mute` | bool | true/false | Muted notes are silent but visible |

## Pitch Reference

### Note-to-MIDI mapping (octave 4 = middle)

| Note | MIDI | Note | MIDI |
|------|------|------|------|
| C3 | 48 | C4 | 60 |
| D3 | 50 | D4 | 62 |
| E3 | 52 | E4 | 64 |
| F3 | 53 | F4 | 65 |
| G3 | 55 | G4 | 67 |
| A3 | 57 | A4 | 69 |
| B3 | 59 | B4 | 71 |

**Formula:** `MIDI = 12 * (octave + 2) + semitone` where C=0, C#=1, D=2...

### Drum map (General MIDI)

| Pitch | Sound | Pitch | Sound |
|-------|-------|-------|-------|
| 36 | Kick | 42 | Closed Hi-Hat |
| 38 | Snare | 46 | Open Hi-Hat |
| 37 | Rim | 49 | Crash |
| 39 | Clap | 51 | Ride |
| 41 | Low Tom | 56 | Cowbell |
| 43 | Mid Tom | 75 | Claves |
| 45 | High Tom | 69 | Cabasa |

## Duration Reference

| Name | Beats | Common use |
|------|-------|------------|
| Whole | 4.0 | Sustained pads |
| Half | 2.0 | Slow melodies |
| Quarter | 1.0 | Standard rhythm |
| Eighth | 0.5 | Faster patterns |
| Sixteenth | 0.25 | Hi-hats, arps |
| Triplet-8th | 0.333 | Shuffle feel |
| Triplet-16th | 0.167 | Fast triplets |
| Dotted-8th | 0.75 | Syncopation |

## Building Patterns

### Basic 4-on-the-floor kick

```python
ableton_clip(operation="create", track_index=0, scene_index=0, length=4)
ableton_clip(operation="add_notes", track_index=0, scene_index=0, notes=[
    {"pitch": 36, "start": 0.0, "duration": 0.5, "velocity": 110},
    {"pitch": 36, "start": 1.0, "duration": 0.5, "velocity": 100},
    {"pitch": 36, "start": 2.0, "duration": 0.5, "velocity": 110},
    {"pitch": 36, "start": 3.0, "duration": 0.5, "velocity": 100},
])
```

### Backbeat snare (2 and 4)

```python
ableton_clip(operation="add_notes", track_index=0, scene_index=0, notes=[
    {"pitch": 38, "start": 1.0, "duration": 0.25, "velocity": 100},
    {"pitch": 38, "start": 3.0, "duration": 0.25, "velocity": 100},
])
```

### Closed hi-hat eighth notes

```python
notes = []
for i in range(8):
    vel = 100 if i % 2 == 0 else 70  # accented downbeats
    notes.append({"pitch": 42, "start": i * 0.5, "duration": 0.25, "velocity": vel})
ableton_clip(operation="add_notes", track_index=0, scene_index=0, notes=notes)
```

### Simple bass line

```python
ableton_clip(operation="create", track_index=1, scene_index=0, length=4)
ableton_clip(operation="add_notes", track_index=1, scene_index=0, notes=[
    {"pitch": 36, "start": 0.0, "duration": 0.75, "velocity": 100},  # C2
    {"pitch": 36, "start": 1.0, "duration": 0.5, "velocity": 90},
    {"pitch": 39, "start": 2.0, "duration": 0.75, "velocity": 100},  # Eb2
    {"pitch": 43, "start": 3.0, "duration": 0.5, "velocity": 90},   # G2
])
```

## Chord Construction

### Common chord shapes (root = C4 = 60)

| Chord | Intervals | Pitches |
|-------|-----------|---------|
| Major | 0, 4, 7 | 60, 64, 67 |
| Minor | 0, 3, 7 | 60, 63, 67 |
| Maj7 | 0, 4, 7, 11 | 60, 64, 67, 71 |
| Min7 | 0, 3, 7, 10 | 60, 63, 67, 70 |
| Dom7 | 0, 4, 7, 10 | 60, 64, 67, 70 |
| Dim | 0, 3, 6 | 60, 63, 66 |
| Aug | 0, 4, 8 | 60, 64, 68 |
| Sus2 | 0, 2, 7 | 60, 62, 67 |
| Sus4 | 0, 5, 7 | 60, 65, 67 |

### Programming a chord progression (Cm - Eb - Bb - Fm)

```python
def chord(root, intervals, start, duration=1.0, velocity=80):
    return [{"pitch": root + i, "start": start, "duration": duration, "velocity": velocity}
            for i in intervals]

minor = [0, 3, 7]
major = [0, 4, 7]

notes = []
notes += chord(60, minor, 0.0, 2.0)   # Cm
notes += chord(63, major, 2.0, 2.0)   # Eb
notes += chord(58, major, 4.0, 2.0)   # Bb
notes += chord(65, minor, 6.0, 2.0)   # Fm

ableton_clip(operation="create", track_index=2, scene_index=0, length=8)
ableton_clip(operation="add_notes", track_index=2, scene_index=0, notes=notes)
```

## Velocity Patterns

Velocity adds humanization and groove:

- **Ghost notes:** velocity 30-50 (barely audible, adds texture)
- **Normal:** velocity 80-100
- **Accents:** velocity 110-127
- **Dynamic curve:** gradually increase/decrease velocity across a phrase

### Humanization pattern

```python
import random
def humanize(notes, vel_range=15, time_range=0.02):
    """Add subtle velocity and timing variations."""
    for n in notes:
        n["velocity"] = max(1, min(127, n["velocity"] + random.randint(-vel_range, vel_range)))
        n["start"] = max(0, n["start"] + random.uniform(-time_range, time_range))
    return notes
```

## Clip Operations

### Check before creating

```python
# Always check if clip exists first
result = ableton_clip(operation="get", track_index=0, scene_index=0)
# If no clip, create one
ableton_clip(operation="create", track_index=0, scene_index=0, length=4)
```

### Loop settings

```python
# Set loop region within clip
ableton_clip(operation="set_loop", track_index=0, scene_index=0, start=0.0, end=4.0)
```

### Duplicate to build variations

```python
# Copy clip to next scene, then modify
ableton_clip(operation="duplicate", track_index=0, scene_index=0)
# Now modify the copy in scene 1
ableton_clip(operation="remove_notes", track_index=0, scene_index=1)
ableton_clip(operation="add_notes", track_index=0, scene_index=1, notes=variation_notes)
```

## Genre-Specific Patterns

### Trap hi-hat pattern (16th + rolls)

```python
notes = []
for i in range(16):
    if i in [6, 7, 14, 15]:  # 32nd-note rolls
        notes.append({"pitch": 42, "start": i * 0.25, "duration": 0.125, "velocity": 90})
        notes.append({"pitch": 42, "start": i * 0.25 + 0.125, "duration": 0.125, "velocity": 70})
    else:
        notes.append({"pitch": 42, "start": i * 0.25, "duration": 0.125, "velocity": 80})
```

### House off-beat hi-hat

```python
notes = [{"pitch": 46, "start": i * 0.5 + 0.25, "duration": 0.25, "velocity": 85}
         for i in range(8)]  # open hi-hat on the "and"
```

### DnB two-step pattern

```python
# Kick on 1, snare at 1.5 beats (6/8 feel in 4/4)
kick_snare = [
    {"pitch": 36, "start": 0.0, "duration": 0.25, "velocity": 110},
    {"pitch": 38, "start": 1.5, "duration": 0.25, "velocity": 100},
    {"pitch": 36, "start": 2.25, "duration": 0.25, "velocity": 100},
    {"pitch": 38, "start": 3.0, "duration": 0.25, "velocity": 105},
]
```

## Common Pitfalls

1. **Overlapping notes at same pitch** — causes retriggering artifacts. Remove before adding.
2. **Velocity 0** — undefined behavior. Use mute flag instead.
3. **Negative start times** — will error. Clip positions start at 0.0.
4. **Duration 0** — inaudible note. Use at least 0.01.
5. **Notes outside clip length** — won't be heard unless loop region covers them.
6. **Drum rack pitch mapping** — depends on the specific rack. GM is a starting point, not gospel.
