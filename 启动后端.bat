@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
echo 正在启动学搭子后端服务...
echo 局域网真机调试模式：监听 0.0.0.0:5000
echo.
set HOST=0.0.0.0
set PORT=5000
python server.py
pause
