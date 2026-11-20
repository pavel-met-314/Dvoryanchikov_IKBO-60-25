@echo off
setlocal
set "registry=https://registry.npmjs.org"

call "%~dp0..\run.bat" --package "bad name" --repository "%registry%"
call "%~dp0..\run.bat" --package express --repository not-a-url
call "%~dp0..\run.bat" --package express --repository "%registry%" --test-mode=false
call "%~dp0..\run.bat" --package express --repository "%registry%" --output graph.jpg
call "%~dp0..\run.bat" --package express --repository "%registry%" --ascii-tree=yes
call "%~dp0..\run.bat" --package express --repository "%registry%" --filter "   "