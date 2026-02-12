#!/usr/bin/env bash
# Install UltimateAbletonMCP Remote Script into Ableton Live's MIDI Remote Scripts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_SCRIPT_SRC="$SCRIPT_DIR/../remote_script/UltimateAbletonMCP"

# Ableton Live MIDI Remote Scripts directories (macOS)
ABLETON_DIRS=(
    "$HOME/Library/Preferences/Ableton/Live 12/User Remote Scripts"
    "$HOME/Library/Preferences/Ableton/Live 11/User Remote Scripts"
    "/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts"
    "/Applications/Ableton Live 12 Standard.app/Contents/App-Resources/MIDI Remote Scripts"
    "/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/MIDI Remote Scripts"
)

TARGET_DIR=""

# Prefer User Remote Scripts directory
for dir in "${ABLETON_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        TARGET_DIR="$dir"
        break
    fi
done

# Create User Remote Scripts if Ableton prefs dir exists
if [[ -z "$TARGET_DIR" ]]; then
    for ver in "Live 12" "Live 11"; do
        prefs="$HOME/Library/Preferences/Ableton/$ver"
        if [[ -d "$prefs" ]]; then
            TARGET_DIR="$prefs/User Remote Scripts"
            mkdir -p "$TARGET_DIR"
            break
        fi
    done
fi

if [[ -z "$TARGET_DIR" ]]; then
    echo "ERROR: Could not find Ableton Live installation."
    echo "Manually symlink: ln -sf $REMOTE_SCRIPT_SRC /path/to/MIDI Remote Scripts/UltimateAbletonMCP"
    exit 1
fi

LINK="$TARGET_DIR/UltimateAbletonMCP"

if [[ -L "$LINK" ]]; then
    echo "Updating existing symlink..."
    rm "$LINK"
elif [[ -d "$LINK" ]]; then
    echo "WARNING: $LINK exists as a directory. Removing..."
    rm -rf "$LINK"
fi

ln -sf "$REMOTE_SCRIPT_SRC" "$LINK"
echo "Installed: $LINK -> $REMOTE_SCRIPT_SRC"
echo ""
echo "Next steps:"
echo "  1. Open Ableton Live"
echo "  2. Preferences > Link, Tempo & MIDI > Control Surface"
echo "  3. Select 'UltimateAbletonMCP'"
echo "  4. Run: uv run ultimate-ableton-mcp"
