@echo off
cd broker
start python listener.py
cd ..
cd agent
start python pluginmanager.py
echo "�ȴ�һ�ᣨԼ12�룩�����������Զ�����"
ping 127.0.0.1>nul
ping 127.0.0.1>nul
ping 127.0.0.1>nul
cd ..
start python manage.py runserver 0.0.0.0:8000
start http://localhost/

