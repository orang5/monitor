@echo off

::start /WAIT systeminfo
set /p system=����ϵͳ��32λ����64λ(32λѡ��0,64λѡ��1):
echo %system%


pause
if %system%==1 (
echo ��ʹ�õ���64λϵͳ
echo ��ʼ��װ
PUSHD %~dp0
cd install
start /WAIT install_64.bat
pause
echo pip install
start /WAIT install_pip.bat
)else (
if %system%==0 (
echo ��ʹ�õ���32λϵͳ
echo ��ʼ��װ
PUSHD %~dp0
cd install
start /WAIT install_32.bat
pause
echo pip install
start /WAIT install_pip_32.bat
))
pause
@echo on