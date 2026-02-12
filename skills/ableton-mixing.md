# Ableton Mixing — Effects, Routing & Automation

Domain knowledge for mixing, effects chains, send/return routing, and automation via `ableton_track` and `ableton_device` tools.

## Signal Flow

```
Track Input → Devices (insert chain) → Sends → Volume/Pan → Output
                                          ↓
                                    Return Tracks → Master
```

Understanding this flow determines WHERE to place effects and HOW to route audio.

## Gain Staging

### Volume reference

Live's mixer: 0.0 (silence) to 1.0 (max). Key reference points:

| Value | Approximate dB | Use |
|-------|----------------|-----|
| 0.0 | -inf | Silent |
| 0.50 | -12 dB | Low background |
| 0.70 | -6 dB | Moderate |
| 0.85 | 0 dB (unity) | Default, no boost/cut |
| 1.0 | +6 dB | Max |

### Setting levels

```python
# Start everything at unity, then pull down
ableton_track(operation="set_volume", track_index=0, value=0.85)  # Drums at unity
ableton_track(operation="set_volume", track_index=1, value=0.80)  # Bass slightly under
ableton_track(operation="set_volume", track_index=2, value=0.70)  # Melody tucked in
ableton_track(operation="set_volume", track_index=3, value=0.65)  # Pad background
```

**Rule of thumb:** Always pull DOWN, never push up. Leave headroom on the master.

## Panning

Pan range: -1.0 (hard left) to 1.0 (hard right), 0.0 = center.

### Standard pan positions

| Element | Pan | Why |
|---------|-----|-----|
| Kick | 0.0 | Always center (low-end stability) |
| Bass | 0.0 | Always center |
| Snare | 0.0 to -0.1 | Center or barely left |
| Hi-hat | 0.2 to 0.4 | Slightly right |
| Lead vocal/synth | 0.0 | Center focus |
| Rhythm guitar L | -0.5 | Left of center |
| Rhythm guitar R | 0.5 | Right of center |
| Pads | -0.3 to 0.3 | Slight spread |

```python
ableton_track(operation="set_pan", track_index=0, value=0.0)   # Kick center
ableton_track(operation="set_pan", track_index=4, value=0.3)   # Hi-hat right
ableton_track(operation="set_pan", track_index=5, value=-0.5)  # Synth L
ableton_track(operation="set_pan", track_index=6, value=0.5)   # Synth R
```

## Send/Return Effects

### Why use sends?

- **CPU efficient** — one reverb shared across tracks
- **Consistent space** — all elements in "same room"
- **Mix control** — adjust wet/dry per-track via send amount

### Setting up reverb and delay returns

```python
# Create return tracks
ableton_track(operation="create", type="return")  # Return A = Reverb
ableton_track(operation="create", type="return")  # Return B = Delay

# Route tracks to returns
ableton_track(operation="set_send", track_index=0, send_index=0, value=0.3)  # Drums → Reverb
ableton_track(operation="set_send", track_index=0, send_index=1, value=0.1)  # Drums → Delay
ableton_track(operation="set_send", track_index=2, send_index=0, value=0.5)  # Lead → Reverb
ableton_track(operation="set_send", track_index=2, send_index=1, value=0.4)  # Lead → Delay
```

### Send levels by element

| Element | Reverb Send | Delay Send | Why |
|---------|-------------|------------|-----|
| Kick | 0.0-0.1 | 0.0 | Keep tight and dry |
| Snare | 0.2-0.4 | 0.1 | Room sound |
| Hi-hat | 0.1-0.2 | 0.0-0.1 | Subtle space |
| Lead | 0.3-0.5 | 0.3-0.5 | Depth and width |
| Pad | 0.4-0.7 | 0.2-0.3 | Atmospheric |
| Vocal | 0.3-0.5 | 0.2-0.4 | Space and interest |

## Device Parameter Control

### Reading device parameters

```python
# List all devices on a track
ableton_device(operation="list", track_index=0)

# Get specific device details including all parameters
ableton_device(operation="get", track_index=0, device_index=0)

# Read a specific parameter
ableton_device(operation="get_param", track_index=0, device_index=0, param=2)
```

### Setting parameters

```python
# By index
ableton_device(operation="set_param", track_index=0, device_index=0, param=2, value=5000.0)

# By name (more readable)
ableton_device(operation="set_param", track_index=0, device_index=0, param="Filter Freq", value=5000.0)
```

### Common effect parameters

**EQ Eight:**
| Param | Range | Description |
|-------|-------|-------------|
| Band 1-8 Gain | -15 to +15 dB | Cut/boost |
| Band 1-8 Freq | 20-20000 Hz | Center frequency |
| Band 1-8 Q | 0.1-18 | Bandwidth (narrow=high) |

**Compressor:**
| Param | Range | Description |
|-------|-------|-------------|
| Threshold | -40 to 0 dB | Where compression starts |
| Ratio | 1:1 to inf:1 | Compression amount |
| Attack | 0.01-30 ms | How fast it grabs |
| Release | 1-1000 ms | How fast it lets go |
| Output Gain | 0-+20 dB | Makeup gain |

**Reverb:**
| Param | Range | Description |
|-------|-------|-------------|
| Decay Time | 0.2-60 s | Tail length |
| Room Size | small to large | Space character |
| Dry/Wet | 0-100% | Balance (100% on returns) |
| Pre-Delay | 0-250 ms | Gap before reverb |

## Automation

### Creating parameter automation in clips

```python
# Get or create automation envelope for a parameter
ableton_device(operation="create_automation", track_index=0, clip_index=0,
               device_index=0, param_index=1)

# Insert automation points
ableton_device(operation="insert_automation_point", track_index=0, clip_index=0,
               device_index=0, param_index=1, time=0.0, value=0.0)
ableton_device(operation="insert_automation_point", track_index=0, clip_index=0,
               device_index=0, param_index=1, time=2.0, value=1.0)
```

### Common automation moves

**Filter sweep (build-up):**
```python
# Gradually open filter over 4 bars
for i in range(16):
    t = i * 1.0  # every beat
    v = i / 15.0  # 0.0 → 1.0
    ableton_device(operation="insert_automation_point",
                   track_index=0, clip_index=0,
                   device_index=0, param_index=2,
                   time=t, value=v)
```

**Volume fade-in:**
```python
ableton_device(operation="insert_automation_point", track_index=0, clip_index=0,
               device_index=0, param_index=1, time=0.0, value=0.0)
ableton_device(operation="insert_automation_point", track_index=0, clip_index=0,
               device_index=0, param_index=1, time=16.0, value=0.85)
```

## Input/Output Routing

### Track routing

```python
# Route MIDI input
ableton_track(operation="set_input_routing", track_index=0, routing_type="Computer Keyboard")

# Route audio output
ableton_track(operation="set_output_routing", track_index=0, routing_type="Sends Only")
```

### Sidechain routing

For sidechain compression (e.g., kick ducking the bass):
1. Route kick's output to bass track's sidechain input
2. Add Compressor on bass with sidechain enabled
3. Set threshold so kick triggers ducking

This requires manual device configuration — use `set_param` to adjust compressor settings after loading.

## Solo/Mute Workflow

### A/B comparison

```python
# Solo drums to check balance
ableton_track(operation="set_solo", track_index=0, enabled=True)
# Listen...
ableton_track(operation="set_solo", track_index=0, enabled=False)

# Mute element to hear mix without it
ableton_track(operation="set_mute", track_index=3, enabled=True)
# Listen to how mix changes...
ableton_track(operation="set_mute", track_index=3, enabled=False)
```

## Mix Bus Processing

The master track typically gets:
1. **EQ** — gentle high-pass at 30Hz to remove sub-rumble
2. **Compressor** — light glue compression (2:1 ratio, slow attack)
3. **Limiter** — ceiling at -0.3 dB to prevent clipping

These are loaded via browser, configured via device parameters.

## Common Pitfalls

1. **Too much reverb** — start dry, add gradually. On sends, set Dry/Wet to 100%.
2. **Phase issues from panning** — always check mono compatibility.
3. **Automating wrong parameter index** — use `get` to verify indices first.
4. **Send to nonexistent return** — check return track count before setting sends.
5. **Volume > 0.85 regularly** — you're boosting, which eats headroom. Pull other tracks down instead.
6. **Forgetting to re-enable automation** — after manual tweaks, call `re_enable_automation`.
