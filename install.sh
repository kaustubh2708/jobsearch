#!/usr/bin/env bash
# Kept for muscle memory. Setup now lives in start.sh (and start.bat on Windows),
# which installs everything on first run and just starts the agent afterwards.
cd "$(dirname "$0")"
echo ""
echo "  Setup is part of ./start.sh now — running it for you."
echo ""
exec ./start.sh "$@"
