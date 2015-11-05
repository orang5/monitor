@echo off
cd broker
start python listener.py
cd ..
cd agent
start python pluginmanager.py
echo "等待一会（约12秒），服务器会自动启动"
ping 127.0.0.1>nul
ping 127.0.0.1>nul
ping 127.0.0.1>nul
cd ..
start python manage.py runserver 0.0.0.0:8000
start http://localhost/

