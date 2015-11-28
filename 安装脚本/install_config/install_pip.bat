@echo off
PUSHD %~dp0
cd ..\..\依赖软件包\64位\pip

pip install distribute-0.7.3.zip
if errorlevel 1 (
echo distribute安装失败
pause)
pip install pip-7.1.2-py2.py3-none-any.whl
if errorlevel 1 (
echo pip-7.1.2安装失败
pause)
pip install PyInstaller-2.1.tar.gz
if errorlevel 1 (
echo PyInstaller安装失败
pause)
pip install setuptools-18.3.1-py2.py3-none-any.whl
if errorlevel 1 (
echo setuptools安装失败
pause)
pip install six-1.9.0-py2.py3-none-any.whl
if errorlevel 1 (
echo six安装失败
pause)
pip install Django-1.8.4-py2.py3-none-any.whl
if errorlevel 1 (
echo Django安装失败
pause)
pip install pymongo-3.0.3-cp27-none-win_amd64.whl
if errorlevel 1 (
echo pymongo安装失败
pause)
pip install pika-0.10.0-py2.py3-none-any.whl
if errorlevel 1 (
echo pika安装失败
pause)
pip install requests-2.7.0-py2.py3-none-any.whl
if errorlevel 1 (
echo requests安装失败
pause)
pip install pyvmomi-5.5.0.2014.1.1.tar.gz
if errorlevel 1 (
echo pyvmomi安装失败
pause)
pip install WMI-1.4.9.zip
if errorlevel 1 (
echo WMI安装失败
pause)
pip install pypiwin32-219-cp27-none-win_amd64.whl
if errorlevel 1 (
echo pypiwin32安装失败
pause)
pip install mongoengine-0.10.0.tar.gz
if errorlevel 1 (
echo mongoengine安装失败
pause)
pause
@echo on