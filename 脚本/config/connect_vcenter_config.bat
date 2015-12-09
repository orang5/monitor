@echo off
cd ../manage
set /p vserver_ip=请输入vcenter服务器ip:
echo 服务器ip为；%vserver_ip%

set /p vserver_user=请输入vcenter服务器用户名:

set /p vserver_pwd=请输入vcenter服务器密码:
echo cd ..\..\>connect_vcenter.bat
echo cd agent\plugins\monitor_vsphere\ >>connect_vcenter.bat

echo start cred_tool.exe %vserver_ip% %vserver_user% %vserver_pwd% >>connect_vcenter.bat

echo 可通过connect_vcenter.bat连接vcenter服务器，如需现在运行请按回车
pause
connect_vcenter.bat
@echo on