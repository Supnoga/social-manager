#!/bin/bash
# Beží na pozadí (spúšťa ho ikonka Social Manager). Po aktualizácii alebo páde appku znova zapne.
cd "$(dirname "$0")/.."
export SM_NO_BROWSER=1
source venv/bin/activate
python -m pip install -q -r requirements.txt >/dev/null 2>&1
fails=0
while true; do
  start=$(date +%s)
  python -m app.main
  code=$?
  [ $code -eq 0 ] && break
  if [ $code -ne 3 ]; then
    echo "$(date) appka spadla (kód $code), spúšťam znova" >> data/chyby.log
    # keď padá hneď po štarte stále dokola, prestaň (inak by sa točila do nekonečna)
    if [ $(( $(date +%s) - start )) -lt 20 ]; then fails=$((fails+1)); else fails=0; fi
    [ $fails -ge 5 ] && break
    sleep 3
  else
    python -m pip install -q -r requirements.txt >/dev/null 2>&1
  fi
done
