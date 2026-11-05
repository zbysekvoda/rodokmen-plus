#!/usr/bin/env bash
# Vydání nové verze pluginu.
#   scripts/release.sh <X.Y.Z> [--push]
# Bez --push: zkontroluje soukromí, zvedne verzi (plugin.json + skills/rodokmen-plus/VERZE), commit + tag vX.Y.Z.
# S --push: navíc pošle main a tag na GitHub a založí GitHub Release přes gh (jen po schválení člověkem).
# Soukromá data pro kontrolu: $RODOKMEN_SOUKROMA_DATA (výchozí ~/Projects/personal/genealogy/data).
set -euo pipefail
cd "$(dirname "$0")/.."

# GitHub Release k tagu (poznámky = commity od předchozího tagu); existující release se přeskočí.
gh_release() {
  local t="v$1" prev notes
  PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
  command -v gh >/dev/null || { echo "gh není nainstalované – release založ ručně: gh release create $t"; return; }
  if gh release view "$t" >/dev/null 2>&1; then echo "Release $t už existuje"; return; fi
  prev=$(git describe --tags --abbrev=0 "$t^" 2>/dev/null || true)
  notes=$(git log --format="- %s" --no-merges ${prev:+$prev..}"$t" | grep -v "^- rodokmen-plus [0-9]" || true)
  gh release create "$t" --verify-tag --latest --title "rodokmen-plus $1" --notes "${notes:-- údržba}" >/dev/null
  echo "Release: https://github.com/zbysekvoda/rodokmen-plus/releases/tag/$t"
}

VER="${1:-}"; PUSH="${2:-}"
[[ "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Použití: $0 <X.Y.Z> [--push]"; exit 2; }
if git rev-parse -q --verify "refs/tags/v$VER" >/dev/null; then
  [[ "$PUSH" == --push ]] || { echo "Tag v$VER už existuje"; exit 1; }
  git push origin main "v$VER"   # verze připravená dřív, teď jen odeslat
  gh_release "$VER"; exit 0
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
  gh_release "$VER"
else
  echo "Push až po schválení: $0 $VER --push  (nebo: git push origin main v$VER)"
fi
