cd ..\..\
cd broker
echo "�����������"
start "�������" python listener.py
cd ..
cd agent
echo "������ش���"
start "��ش���" python pluginmanager.py
echo "�ȴ�һ�ᣨԼ12�룩�����������Զ�����"
ping 127.0.0.1>nul
ping 127.0.0.1>nul
ping 127.0.0.1>nul
cd ..
echo "����������"
start "������" python manage.py runserver 0.0.0.0:80
start http://localhost/

