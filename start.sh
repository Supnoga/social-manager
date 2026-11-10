#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Chýba Python 3. Otváram stránku na stiahnutie."
  open https://www.python.org/downloads/ 2>/dev/null || xdg-open https://www.python.org/downloads/
  read -p "Stlač Enter..." ; exit 1
fi
if [ ! -d venv ]; then echo "Prvé spustenie - pripravujem appku..."; python3 -m venv venv; fi
source venv/bin/activate
python -m pip install -q --upgrade pip >/dev/null 2>&1
python -m pip install -q -r requirements.txt
echo ""
echo " Social Manager beží na http://localhost:8765"
echo " Toto okno nechaj otvorené (zatvorením appku vypneš)."
trap 'exit 0' INT
while true; do
  python -m app.main
  code=$?
  if [ $code -eq 0 ] || [ $code -eq 130 ]; then break; fi
  if [ $code -eq 3 ]; then echo "Aktualizujem a znova spúšťam..."; else echo "Appka spadla (kód $code) – o 3 sekundy ju spúšťam znova. Záznam je v data/chyby.log"; echo "$(date) pad, kod $code" >> data/chyby.log; sleep 3; fi
  export SM_NO_BROWSER=1
done
