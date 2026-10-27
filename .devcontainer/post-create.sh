#!/usr/bin/env bash
# Runs once when the Codespace is created ; the same steps as the README's laptop setup.
set -euo pipefail

curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh
uv sync --group server --frozen

# .env without the empty keys : langgraph dev lets .env values win over the
# environment, and an empty COURSE_API_KEY= would hide the Codespaces secret.
if [ ! -f .env ]; then
  grep -vE '^[A-Z_]+=$' .env.example > .env
fi

if [ -z "${COURSE_API_KEY:-}" ]; then
  echo
  echo "COURSE_API_KEY is not set. Add it as a Codespaces secret (github.com/settings/codespaces,"
  echo "repository access for this repository) and rebuild or restart the Codespace,"
  echo "or add the line COURSE_API_KEY=<key> to .env."
fi
