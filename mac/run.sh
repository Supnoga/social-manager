#!/bin/bash
# Beží na pozadí (spúšťa ho ikonka Social Manager alebo Mac po prihlásení). Po aktualizácii alebo páde appku znova zapne.
cd "$(dirname "$0")/.."
export SM_NO_BROWSER=1
export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# už beží (napr. ikonka aj automatický štart naraz): druhá kópia netreba
if curl -sf -m 2 "http://localhost:${SM_PORT:-8765}/api/ping" >/dev/null 2>&1; then exit 0; fi
source venv/bin/activate
python -m pip install -q -r requirements.txt >/dev/null 2>&1
say() { osascript -e "display notification \"$1\" with title \"Social Manager\"" >/dev/null 2>&1; }
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
    # po aktualizácii nenabehla: vráť predošlú verziu (je odložená v data/prev_code) a novú už neskúšaj
    if [ $fails -eq 3 ] && [ -f data/prev_code/app/main.py ] && [ "$(cat data/prev_code/VERSION 2>/dev/null)" != "$(cat VERSION 2>/dev/null)" ]; then
      cat VERSION >> data/skip_version; echo >> data/skip_version
      echo "$(date) verzia $(cat VERSION) nenabehla, vraciam $(cat data/prev_code/VERSION)" >> data/chyby.log
      for item in data/prev_code/*; do
        name="$(basename "$item")"
        rm -rf "./$name"; cp -R "$item" "./$name"
      done
      say "Nová verzia nenabehla, vrátil som predošlú."
      python -m pip install -q -r requirements.txt >/dev/null 2>&1
      continue
    fi
    if [ $fails -ge 6 ]; then
      say "Appka sa nedá zapnúť. Napíš Claudovi, pozrie sa na to."
      break
    fi
    sleep 3
  else
    fails=0
    python -m pip install -q -r requirements.txt >/dev/null 2>&1
  fi
done
