
@echo off
echo �����������ԱȨ������
echo ���뵱ǰĿ¼
PUSHD %~dp0
echo ��ǰMONITOR_HOMEΪ %MONITOR_HOME% �����޸��밴�س���
pause
cd ..\
setx MONITOR_HOME "%cd%"
cd ��װ�ű�
echo %MONITOR_HOME%

echo ��ǰpath��������Ϊ��%path%
echo ���û�������"
pause
setx path "%path%;C:\Windows\Microsoft.NET\Framework64\v3.5;C:\Windows\Microsoft.NET\Framework64\v4.0.30319;C:\Python27;C:\Python27\Scripts;C:\Program Files (x86)\RabbitMQ Server\rabbitmq_server-3.5.2\sbin;C:\Program Files\MongoDB\Server\3.0\bin" /M
::echo ��ǰpath��������Ϊ��%path%


pause

