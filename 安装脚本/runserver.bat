<<<<<<< HEAD
cd ..
cd broker
echo "�����������"
start "�������" python listener.py
cd ..
cd agent
echo "������ش���"
start "��ش���" python pluginmanager.py
=======
@echo off
cd broker
start python listener.py
cd ..
cd agent
start python pluginmanager.py
>>>>>>> kongwu/master
echo "�ȴ�һ�ᣨԼ12�룩�����������Զ�����"
ping 127.0.0.1>nul
ping 127.0.0.1>nul
ping 127.0.0.1>nul
cd ..
<<<<<<< HEAD
echo "����������"
start "������" python manage.py runserver 0.0.0.0:8000
=======
start python manage.py runserver 0.0.0.0:8000
>>>>>>> kongwu/master
start http://localhost/

