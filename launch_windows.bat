@echo off
echo Starting Drug Card Creator...
start /B python app.py
timeout /t 2 /nobreak >nul
start http://localhost:5000
