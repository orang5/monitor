echo ��ʼ��װ
start /WAIT systeminfo
set system=
set /p system=����ϵͳ��32λ����64λ(32λѡ��0,64λѡ��1):
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
echo ���û�������
start /WAIT #setenv.bat
pause