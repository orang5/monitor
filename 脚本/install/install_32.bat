@echo off
PUSHD %~dp0
cd ..\..\..\依赖软件包\64位

dotnetfx35.exe
if errorlevel 1 (
echo dotnetfx35安装失败
pause)
dotNetFx40_Full_x86_x64.exe
if errorlevel 1 (
echo dotnetfx40安装失败
pause)
cd ..\32位
mongodb-win32-i386-3.0.6.zip
if errorlevel 1 (
echo mongodb安装失败 
pause)
otp_win32_17.5.exe
if errorlevel 1 (
echo otp安装失败 
pause)
python-2.7.9.msi
if errorlevel 1 (
echo python安装失败 
pause)
pywin32-219.win32-py2.7.exe
if errorlevel 1 (
echo pywin32安装失败 
pause)
cd ..\64位
rabbitmq-server-3.5.2.exe
if errorlevel 1 (
echo rabbitmq安装失败 
pause)
cd vSphereSDK
"Microsoft WSE 3.0.msi"
if errorlevel 1 (
echo vspheresdk安装失败 
pause)
pause
exit
@echo on