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
cd ..\32λ
mongodb-win32-i386-3.0.6.zip
if errorlevel 1 (
echo mongodb��װʧ�� 
pause)
otp_win32_17.5.exe
if errorlevel 1 (
echo otp��װʧ�� 
pause)
python-2.7.9.msi
if errorlevel 1 (
echo python��װʧ�� 
pause)
pywin32-219.win32-py2.7.exe
if errorlevel 1 (
echo pywin32��װʧ�� 
pause)
cd ..\64λ
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