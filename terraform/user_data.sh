#!/bin/bash
set -e

apt-get update && apt-get upgrade -y
apt-get install -y git

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

cd /opt
git clone https://github.com/Sandrog112/parking-assistant.git
cd parking-assistant

uv sync

uv run python -m parking_assistant.rag.knowledge

nohup uv run uvicorn parking_assistant.mcp.server:app --host 0.0.0.0 --port 8000 &
