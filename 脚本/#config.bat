echo �����������ԱȨ������
PUSHD %~dp0
echo ����mongodbע��Ϊ����
pause
cd C:\monitor\data\
echo >mongodb.Log
mongod --dbpath C:\monitor\data\ --logpath C:\monitor\data\mongodb.Log --install --serviceName mongodb

echo ����rabbitmq
pause
start rabbitmq-server
@echo on
echo ����û�
pause
start rabbitmqctl add_user monitor root
start rabbitmqctl list_users 
pause
echo ������
pause
start rabbitmqctl set_permissions -p / monitor ".*" ".*" ".*"
start rabbitmqctl list_permissions -p /

echo ����vcenter����������
cd config
connect_vcenter_config.bat

echo �޸�config.py��monitor_vsphere.json��config.py�е�ip��Ϊrabbitmq server ip��monitor_vsphere.json�е�ip���û�����Ϊvcenter server��ip���û�����
pause
cd ..\..\
start common\config.py
start agent\plugins\monitor_vsphere.json


pause
