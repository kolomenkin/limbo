@echo off
setlocal

%~d0
cd "%~dp0"
echo dir: %CD%

REM Setup python environment (OPTIONAL):
call :find_path_file dev.bat DEV_FULLPATH
if not "%DEV_FULLPATH%" == "" (
	call "%DEV_FULLPATH%"
)

REM set LIMBO_IS_DEBUG=1
set LIMBO_WEB_SERVER=cherrypy
set LIMBO_LISTEN_HOST=127.0.0.1
set LIMBO_LISTEN_PORT=8080

python --version

REM install dependencies
python -m pip install -r requirements.txt

python server.py

pause
goto :eof

:find_path_file
	set %2=%~$PATH:1
	goto :eof
