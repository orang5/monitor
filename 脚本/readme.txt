以#开头的脚本需要以管理员身份运行
install.bat：
  为安装与环境设置总脚本
  （详细脚本安放在install文件夹）
#setenv.bat:
  设置环境变量
#config.bat：
  用于设置数据库服务,配置rabbitmq,连接vcenter，以及打开需要修改的配置文件
  （详细脚本安放在config文件夹）
manage文件夹：管理脚本
  clear_document用于清空数据库
  dump_document用于下载数据库数据
  runserver用于启动服务器