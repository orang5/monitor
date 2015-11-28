
@echo off
echo 进入当前目录
PUSHD %~dp0
echo 当前MONITOR_HOME为 %MONITOR_HOME% 如需修改请按回车键
pause
cd ..\..\
setx MONITOR_HOME "%cd%"
cd 安装脚本
echo %MONITOR_HOME%

echo 当前path环境变量为：%path%
echo 设置环境变量"
pause
setx path "%path%;C:\Windows\Microsoft.NET\Framework64\v3.5;C:\Windows\Microsoft.NET\Framework64\v4.0.30319;C:\Python27;C:\Python27\Scripts;C:\Program Files (x86)\RabbitMQ Server\rabbitmq_server-3.5.2\sbin;C:\Program Files\MongoDB\Server\3.0\bin" /M
::echo 当前path环境变量为：%path%

echo 打开config.py和monitor_vsphere.json
pause
start ..\common\config.py
start ..\agent\plugins\monitor_vsphere.json
pause

