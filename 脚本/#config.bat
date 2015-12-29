echo 本程序需管理员权限运行
PUSHD %~dp0
echo “将mongodb注册为服务”
pause
cd C:\monitor\data\
echo >mongodb.Log
mongod --dbpath C:\monitor\data\ --logpath C:\monitor\data\mongodb.Log --install --serviceName mongodb

echo 启动rabbitmq
pause
start rabbitmq-server
@echo on
echo 添加用户
pause
start rabbitmqctl add_user monitor root
start rabbitmqctl list_users 
pause
echo 添加许可
pause
start rabbitmqctl set_permissions -p / monitor ".*" ".*" ".*"
start rabbitmqctl list_permissions -p /

echo 配置vcenter服务器连接
cd config
connect_vcenter_config.bat

echo 修改config.py和monitor_vsphere.json（config.py中的ip改为rabbitmq server ip；monitor_vsphere.json中的ip和用户名改为vcenter server的ip和用户名）
pause
cd ..\..\
start common\config.py
start agent\plugins\monitor_vsphere.json


pause
