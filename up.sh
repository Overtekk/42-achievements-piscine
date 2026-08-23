#!/usr/bin/env bash

cd "$(dirname "$0")"

pkill -f "python.*main.py" && echo "bot killed" || echo "bot not running"

uv run main.py > bot.log 2>&1 &
disown
echo "bot launched, logs in bot.log"
