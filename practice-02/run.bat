@echo off
py "%~dp0src\main.py" %*
exit /b %errorlevel%