@echo off
setlocal
cd /d %~dp0

if not exist node_modules (
  npm install
)

if not exist backend\.venv\Scripts\python.exe (
  python -m venv backend\.venv
  backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)

npm run dev
