@echo off
PUSHD %~dp0
cd ..\..\���������\64λ

dotnetfx35.exe
if errorlevel 1 (
echo dotnetfx35��װʧ��
pause)
dotNetFx40_Full_x86_x64.exe
if errorlevel 1 (
echo dotnetfx40��װʧ��
pause)
mongodb-win32-x86_64-2008plus-ssl-3.0.2-signed.msi
if errorlevel 1 (
echo mongodb��װʧ�� 
pause)
otp_win64_17.5.exe
if errorlevel 1 (
echo otp��װʧ�� 
pause)
python-2.7.9.amd64.msi
if errorlevel 1 (
echo python��װʧ�� 
pause)
pywin32-219.win-amd64-py2.7.exe
if errorlevel 1 (
echo pywin32��װʧ�� 
pause)
rabbitmq-server-3.5.2.exe
if errorlevel 1 (
echo rabbitmq��װʧ�� 
pause)
cd vSphereSDK
"Microsoft WSE 3.0.msi"
if errorlevel 1 (
echo vspheresdk��װʧ�� 
pause)
pause
@echo on