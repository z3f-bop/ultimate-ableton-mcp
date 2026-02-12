# Ableton Sound Design — Devices, Browser & Presets

Domain knowledge for navigating instruments, loading devices, managing presets, and rack chains via `ableton_device` and `ableton_browser` tools.

## Browser Navigation

### Category hierarchy

```
instruments/     → Synths, samplers (Analog, Operator, Simpler, Wavetable...)
sounds/          → Preset packs organized by type
drums/           → Drum racks and kits
audio_effects/   → EQ, Compressor, Reverb, Delay, Distortion...
midi_effects/    → Arpeggiator, Chord, Scale, Note Length...
```

### Browsing and loading

```python
# Get top-level categories
ableton_browser(operation="get_tree", category="instruments")

# Navigate deeper into a category
ableton_browser(operation="get_items", path="instruments/Analog")

# Load an instrument onto a track by URI
ableton_browser(operation="load_item", track_index=0, uri="query:Analog")
```

### Loading workflow

1. Browse to find the item
2. Note the URI from the browser result
3. Load onto target track using the URI
4. Adjust parameters after loading

## Live's Built-in Instruments

### Analog (Subtractive Synth)
- 2 oscillators + sub, filters, envelopes, LFOs
- Best for: basses, leads, pads, classic synth sounds
- Key params: Osc waveform, Filter cutoff/resonance, Amp envelope

### Operator (FM Synth)
- 4 operators with multiple algorithms
- Best for: bells, metallic sounds, complex timbres, basses
- Key params: Operator ratios, Algorithm, Tone

### Wavetable
- Wavetable scanning with sub oscillator
- Best for: evolving pads, modern leads, cinematic textures
- Key params: Wavetable position, Sub amount, Filter

### Simpler / Sampler
- Sample-based playback
- Simpler: one-shot or looped samples
- Sampler: multi-sample, zones, modulation matrix
- Best for: working with audio samples, creating instruments from recordings

### Drift
- Virtual analog with character
- Best for: warm analog-style sounds, lo-fi textures
- Key params: Shape, Drift amount, Filter

### Drum Rack
- 128 pads, each holding a device chain
- Best for: drum kits, layered percussion, sample banks
- Key params: Per-pad volume, pan, pitch, sends

## Device Parameter Manipulation

### Discovering parameters

```python
# Get full device info with all parameters
result = ableton_device(operation="get", track_index=0, device_index=0)
# Returns: name, class_name, parameters (with index, name, value, min, max)
```

### Parameter types

| Type | Range | Example |
|------|-------|---------|
| Continuous | min-max float | Filter Freq: 20.0-20000.0 |
| On/Off | 0.0 or 1.0 | Device On: 0.0/1.0 |
| Quantized | discrete steps | Waveform: 0=Sine, 1=Saw, 2=Square... |

### Modifying sound character

```python
# Open the filter
ableton_device(operation="set_param", track_index=0, device_index=0,
               param="Filter Freq", value=8000.0)

# Increase resonance for more bite
ableton_device(operation="set_param", track_index=0, device_index=0,
               param="Filter Res", value=0.6)

# Slow down the attack for pad-like onset
ableton_device(operation="set_param", track_index=0, device_index=0,
               param="Amp Attack", value=500.0)
```

## Preset Management

### Browsing presets

```python
# Get available presets for a device
ableton_device(operation="get_presets", track_index=0, device_index=0)
```

### Loading presets

```python
# Set preset by index
ableton_device(operation="set_preset", track_index=0, device_index=0, preset_index=2)
```

### Preset workflow
1. Load device from browser
2. Browse presets as starting point
3. Modify parameters to taste
4. Automate parameters for movement

## Audio Effects Reference

### Essential mixing effects

| Effect | Purpose | Key Params |
|--------|---------|------------|
| EQ Eight | Frequency shaping | Band freq, gain, Q |
| Compressor | Dynamic control | Threshold, ratio, attack, release |
| Glue Compressor | Bus glue | Threshold, ratio, makeup |
| Limiter | Peak control | Ceiling, gain |
| Utility | Gain staging, mono, phase | Gain, width, mono |

### Creative effects

| Effect | Purpose | Key Params |
|--------|---------|------------|
| Reverb | Space and depth | Decay, size, dry/wet |
| Delay | Rhythmic echoes | Time, feedback, dry/wet |
| Chorus-Ensemble | Width and movement | Rate, amount |
| Phaser-Flanger | Modulation | Rate, feedback |
| Saturator | Warmth and grit | Drive, type |
| Overdrive | Aggressive distortion | Drive, tone |
| Redux | Bit crushing, lo-fi | Bit depth, downsample |
| Auto-Pan | Stereo movement | Rate, amount, shape |
| Beat Repeat | Glitch and stutter | Grid, variation |
| Grain Delay | Granular texture | Spray, frequency |

## MIDI Effects

Load before instruments in the chain:

| Effect | Purpose | Key Params |
|--------|---------|------------|
| Arpeggiator | Auto-arpeggiate held chords | Style, rate, steps |
| Chord | Add intervals to notes | Shift 1-6 |
| Scale | Force notes to scale | Base, type |
| Note Length | Uniform note durations | Length, gate |
| Random | Pitch/velocity randomization | Chance, range |
| Velocity | Remap velocity curve | Min, max, curve |

## Rack Chains

### Understanding racks

Racks contain chains, each chain holds devices:

```
Instrument Rack
├── Chain 1: "Bass Layer"
│   ├── Analog (low settings)
│   └── EQ Eight
├── Chain 2: "Top Layer"
│   ├── Wavetable (bright settings)
│   └── Compressor
└── Macro Controls (8 knobs mapping to inner params)
```

### Inspecting rack contents

```python
# Check if device has chains
result = ableton_device(operation="get", track_index=0, device_index=0)
# Look for can_have_chains: true

# Get chain details
ableton_device(operation="get_chains", track_index=0, device_index=0)
```

## Sound Design Recipes

### Thick bass

1. Load Analog
2. Set Osc 1 to Saw, Osc 2 to Square (detuned -7 cents)
3. Filter cutoff ~400 Hz, resonance ~0.3
4. Short amp attack (1ms), medium release (200ms)
5. Add Saturator after for warmth

### Ambient pad

1. Load Wavetable
2. Slow wavetable position sweep (automate or LFO)
3. Long attack (500ms+), long release (2s+)
4. Reverb send at 0.6+, delay send at 0.3
5. Chorus for width

### Punchy kick

1. Load Simpler with kick sample
2. Tight amp envelope (attack 0, decay 200ms)
3. Add Utility → mono, slight gain boost
4. Compressor: fast attack, ratio 4:1
5. EQ: boost 60Hz, cut 300Hz mud

### Crispy hi-hat

1. Load Simpler with hat sample
2. Very short decay (50-100ms)
3. High-pass filter at 5kHz
4. Subtle Saturator for presence
5. Keep velocity variation for groove

## Common Pitfalls

1. **Loading to wrong track** — verify track_index before `load_item`
2. **Parameter name mismatch** — names are device-specific, use `get` to discover them
3. **Quantized params** — setting 0.5 on an on/off param gives undefined results
4. **Chain navigation** — rack chains need separate device indices
5. **Effect order matters** — EQ before compression vs after changes character entirely
6. **Too many effects** — CPU adds up. Freeze tracks with heavy chains.
