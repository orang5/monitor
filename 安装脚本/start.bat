echo 开始安装
start /WAIT systeminfo
set system=
set /p system=请问系统是32位还是64位(32位选择0,64位选择1):
echo %system%
pause
if %system%==1 (
PUSHD %~dp0
cd install_config
start /WAIT install_64.bat
pause
echo pip install
start /WAIT install_pip.bat
)else (
if %system%==0 (
PUSHD %~dp0
cd install_config
start /WAIT install_32.bat
pause
echo pip install
start /WAIT install_pip_32.bat
))
pause
echo 设置环境变量
start /WAIT #setenv.bat
pause