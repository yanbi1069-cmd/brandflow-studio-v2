@echo off
setlocal
cd /d "%~dp0"
python start_agent.py
if errorlevel 1 pause

