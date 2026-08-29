#!/usr/bin/env bash
# Post a catalogue chat turn and poll until done (or waiting on ASK).
#   ./run-chat.sh --list
#   ./run-chat.sh shopassist_case_ask
#   ./run-chat.sh --all          # post every row in chats.json
#   WAIT=1 ./run-chat.sh --all   # also wait for each to finish
set -euo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/run_chat.py" "$@"
