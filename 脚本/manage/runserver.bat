cd ..\..\
cd broker
echo "启动传输代理"
start "传输代理" python listener.py
cd ..
cd agent
echo "启动监控代理"
start "监控代理" python pluginmanager.py
echo "等待一会（约12秒），服务器会自动启动"
ping 127.0.0.1>nul
ping 127.0.0.1>nul
ping 127.0.0.1>nul
cd ..
echo "启动服务器"
start "服务器" python manage.py runserver

