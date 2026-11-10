@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Social Manager
set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY goto nopython
if not exist venv (
  echo Prve spustenie - pripravujem appku, chvilu to potrva...
  %PY% -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -q --upgrade pip >nul 2>nul
python -m pip install -q -r requirements.txt
echo.
echo  Social Manager bezi na http://localhost:8765
echo  Toto okno nechaj otvorene (zatvorenim appku vypnes).
echo.
:run
python -m app.main
set CODE=%errorlevel%
set SM_NO_BROWSER=1
if %CODE%==0 goto end
if %CODE%==3 (
  echo Aktualizujem a znova spustam...
  goto run
)
echo Appka spadla - o 3 sekundy ju spustam znova.
timeout /t 3 >nul
goto run
:end
pause
exit /b

:nopython
echo Chyba Python. Otvaram stranku na stiahnutie.
echo Pri instalacii ZASKRTNI "Add python.exe to PATH" a potom spusti start.bat znova.
start https://www.python.org/downloads/
pause
