@echo off
cd ../manage
set /p vserver_ip=������vcenter������ip:
echo ������ipΪ��%vserver_ip%

set /p vserver_user=������vcenter�������û���:

set /p vserver_pwd=������vcenter����������:
echo cd ..\..\>connect_vcenter.bat
echo cd agent\plugins\monitor_vsphere\ >>connect_vcenter.bat

echo start cred_tool.exe %vserver_ip% %vserver_user% %vserver_pwd% >>connect_vcenter.bat

echo ��ͨ��connect_vcenter.bat����vcenter���������������������밴�س�
pause
connect_vcenter.bat
@echo on