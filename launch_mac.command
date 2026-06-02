#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Drug Card Creator..."
python3 app.py &
sleep 2
open http://localhost:5000 2>/dev/null || xdg-open http://localhost:5000
