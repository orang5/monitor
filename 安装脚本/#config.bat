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
pause
