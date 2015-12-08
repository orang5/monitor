@echo off

::start /WAIT systeminfo
set /p system=请问系统是32位还是64位(32位选择0,64位选择1):
echo %system%


pause
if %system%==1 (
echo 您使用的是64位系统
echo 开始安装
PUSHD %~dp0
cd install
start /WAIT install_64.bat
pause
echo pip install
start /WAIT install_pip.bat
)else (
if %system%==0 (
echo 您使用的是32位系统
echo 开始安装
PUSHD %~dp0
cd install
start /WAIT install_32.bat
pause
echo pip install
start /WAIT install_pip_32.bat
))
pause
@echo on