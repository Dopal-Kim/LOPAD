#!/bin/bash
# LOPAD SessionStart hook: Claude Code on the web 세션에서 의존성을 준비한다.
# - npm install   : Phaser/Vite/TypeScript (게임 시스템·UI 파트 빌드)
# - Pillow        : .claude/skills/pixel-art-studio (아트 파트)
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

if [ -f package.json ]; then
  npm install --no-audit --no-fund
fi

if ! python3 -c "import PIL" >/dev/null 2>&1; then
  python3 -m pip install --quiet pillow
fi
