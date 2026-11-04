#!/usr/bin/env bash
# Vydání nové verze pluginu.
#   scripts/release.sh <X.Y.Z> [--push]
# Bez --push: zkontroluje soukromí, zvedne verzi (plugin.json + skills/rodokmen-plus/VERZE), commit + tag vX.Y.Z.
# S --push: navíc pošle main a tag na GitHub (jen po schválení člověkem).
# Soukromá data pro kontrolu: $RODOKMEN_SOUKROMA_DATA (výchozí ~/Projects/personal/genealogy/data).
set -euo pipefail
cd "$(dirname "$0")/.."

VER="${1:-}"; PUSH="${2:-}"
[[ "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Použití: $0 <X.Y.Z> [--push]"; exit 2; }
if git rev-parse -q --verify "refs/tags/v$VER" >/dev/null; then
  [[ "$PUSH" == --push ]] || { echo "Tag v$VER už existuje"; exit 1; }
  git push origin main "v$VER"   # verze připravená dřív, teď jen odeslat
  echo "Odesláno. Release: https://github.com/zbysekvoda/rodokmen-plus/releases/tag/v$VER"; exit 0
fi
[[ "$(git branch --show-current)" == main ]] || { echo "Vydává se z main"; exit 1; }

DATA="${RODOKMEN_SOUKROMA_DATA:-$HOME/Projects/personal/genealogy/data}"
git add -A
python3 -I scripts/kontrola_soukromi.py "$DATA"

python3 -I - "$VER" <<'EOF'
import json, sys
ver = sys.argv[1]
p = ".claude-plugin/plugin.json"
d = json.load(open(p, encoding="utf-8")); d["version"] = ver
open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
open("skills/rodokmen-plus/VERZE", "w", encoding="utf-8").write(ver + "\n")
EOF

git add -A
git commit -q -m "rodokmen-plus $VER" -m "$(git diff --cached --stat | tail -1)"
git tag -a "v$VER" -m "rodokmen-plus $VER"
echo "Připraveno: v$VER ($(git rev-parse --short HEAD))"

if [[ "$PUSH" == --push ]]; then
  git push origin main "v$VER"
  echo "Odesláno. Release: https://github.com/zbysekvoda/rodokmen-plus/releases/tag/v$VER"
else
  echo "Push až po schválení: $0 $VER --push  (nebo: git push origin main v$VER)"
fi
