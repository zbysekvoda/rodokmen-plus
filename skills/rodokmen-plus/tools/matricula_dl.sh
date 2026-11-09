#!/bin/bash
# matricula_dl.sh URL OUT  -- stáhne obrázek z img.data.matricula-online.eu (URL s csrf+ctrl z prohlížeče)
# Přes sdílenou mezipaměť (cache.py): stejný snímek se podruhé vezme z disku.
tok=$(echo "$1" | sed -E 's/.*csrf=([^&]+).*/\1/')
PY=python3; $PY -c "" 2>/dev/null || PY=python; $PY -c "" 2>/dev/null || PY="py -3"
$PY -I "$(dirname "$0")/cache.py" soubor "$1" "$2" -- -s -A "Mozilla/5.0" -e "https://data.matricula-online.eu/" -b "shared_csrftoken=$tok"; file "$2" | cut -d, -f1,8
