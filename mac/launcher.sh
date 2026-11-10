#!/bin/bash
# Ikonka "Social Manager": pri prvom spustení appku nainštaluje, potom ju len zapne a otvorí v prehliadači.
APPDIR="$HOME/Library/Application Support/SocialManager"
RES="$(cd "$(dirname "$0")/../Resources" && pwd)"
URL="http://localhost:8765"
export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

say() { osascript -e "display notification \"$1\" with title \"Social Manager\"" >/dev/null 2>&1; }
alert() { osascript -e "display dialog \"$1\" with title \"Social Manager\" buttons {\"OK\"} default button 1 with icon caution" >/dev/null 2>&1; }

# už beží -> len otvor
if curl -sf -m 2 "$URL/api/ping" >/dev/null 2>&1; then open "$URL"; exit 0; fi
# beží ešte stará verzia z Terminálu -> vypni ju
if curl -s -m 2 "$URL/" >/dev/null 2>&1; then
  pkill -f "app.main" >/dev/null 2>&1; sleep 2
  osascript -e 'tell application "Terminal" to close (every window whose name contains "start.command")' >/dev/null 2>&1
fi

# Python
PY=""
for c in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$c" ] && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then PY="$c"; fi
done
if [ -z "$PY" ]; then
  alert "Chýba Python. Otvorím stránku – stiahni a nainštaluj Python, potom znova klikni na ikonku."
  open "https://www.python.org/downloads/"; exit 1
fi

mkdir -p "$APPDIR/data"
ver() { cat "$1/VERSION" 2>/dev/null || echo 0; }
newest() { printf '%s\n%s\n' "$1" "$2" | sort -V | tail -1; }

# kód appky: prvá inštalácia alebo novšia verzia v ikonke
if [ ! -f "$APPDIR/app/main.py" ] || { [ "$(ver "$RES/social-manager")" != "$(ver "$APPDIR")" ] && [ "$(newest "$(ver "$RES/social-manager")" "$(ver "$APPDIR")")" = "$(ver "$RES/social-manager")" ]; }; then
  for item in "$RES/social-manager/"*; do
    name="$(basename "$item")"
    [ "$name" = "data" ] && continue
    rm -rf "$APPDIR/$name"; cp -R "$item" "$APPDIR/$name"
  done
fi

# prenesie dáta zo starej verzie (zip v Stiahnutých / na Ploche)
if [ ! -f "$APPDIR/data/app.db" ]; then
  for old in "$HOME/Downloads/social-manager/data" "$HOME/Desktop/social-manager/data" "$HOME/Documents/social-manager/data" "$HOME/Downloads/social-manager 2/data"; do
    if [ -f "$old/app.db" ]; then
      cp -R "$old/." "$APPDIR/data/"
      # cesty k súborom v databáze presmeruje na nové miesto
      "$PY" - "$old" "$APPDIR/data" <<'PYEOF' >> "$APPDIR/data/spustanie.log" 2>&1
import sqlite3, sys
old, new = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/")
con = sqlite3.connect(new + "/app.db")
for table, in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    for col in con.execute(f"PRAGMA table_info({table})").fetchall():
        if col[2].upper() in ("TEXT", ""):
            con.execute(f"UPDATE {table} SET {col[1]}=REPLACE({col[1]}, ?, ?) WHERE {col[1]} LIKE ?", (old, new, f"%{old}%"))
con.commit()
PYEOF
      break
    fi
  done
fi

cd "$APPDIR"
if [ ! -x venv/bin/python ]; then
  say "Prvé spustenie – pripravujem appku (asi 1–2 minúty)…"
  "$PY" -m venv venv >> data/spustanie.log 2>&1
  venv/bin/python -m pip install -q --upgrade pip >> data/spustanie.log 2>&1
  if ! venv/bin/python -m pip install -q -r requirements.txt >> data/spustanie.log 2>&1; then
    alert "Inštalácia sa nepodarila (skontroluj internet) a skús znova."; rm -rf venv; exit 1
  fi
fi

chmod +x mac/run.sh
nohup /bin/bash mac/run.sh >> data/spustanie.log 2>&1 &
disown

for i in $(seq 1 120); do
  sleep 1
  if curl -sf -m 2 "$URL/api/ping" >/dev/null 2>&1; then open "$URL"; exit 0; fi
done
alert "Appka sa nezapla. Skús znova kliknúť na ikonku. Ak to nepomôže, pošli Claudovi súbor data/chyby.log."
exit 1
