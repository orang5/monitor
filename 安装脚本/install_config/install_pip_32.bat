@echo off
PUSHD %~dp0
cd ..\..\���������\64λ\pip

pip install distribute-0.7.3.zip
if errorlevel 1 (
echo distribute��װʧ��
pause)
pip install pip-7.1.2-py2.py3-none-any.whl
if errorlevel 1 (
echo pip-7.1.2��װʧ��
pause)
pip install PyInstaller-2.1.tar.gz
if errorlevel 1 (
echo PyInstaller��װʧ��
pause)
pip install setuptools-18.3.1-py2.py3-none-any.whl
if errorlevel 1 (
echo setuptools��װʧ��
pause)
pip install six-1.9.0-py2.py3-none-any.whl
if errorlevel 1 (
echo six��װʧ��
pause)
pip install Django-1.8.4-py2.py3-none-any.whl
if errorlevel 1 (
echo Django��װʧ��
pause)

cd ..\..\32λ\pip
pip install pymongo-3.0.3-cp27-none-win32.whl
if errorlevel 1 (
echo pymongo��װʧ��
pause)
cd ..\..\64λ\pip

pip install pika-0.10.0-py2.py3-none-any.whl
if errorlevel 1 (
echo pika��װʧ��
pause)
pip install requests-2.7.0-py2.py3-none-any.whl
if errorlevel 1 (
echo requests��װʧ��
pause)
pip install pyvmomi-5.5.0.2014.1.1.tar.gz
if errorlevel 1 (
echo pyvmomi��װʧ��
pause)
pip install WMI-1.4.9.zip
if errorlevel 1 (
echo WMI��װʧ��
pause)

cd ..\..\32λ\pip
pip install pypiwin32-219-cp27-none-win32.whl
if errorlevel 1 (
echo pypiwin32��װʧ��
pause)
cd ..\..\64λ\pip

pip install mongoengine-0.10.0.tar.gz
if errorlevel 1 (
echo mongoengine��װʧ��
pause)
pause
@echo on
