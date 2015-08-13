# -*- coding: utf-8 -*-
import time, pythoncom, wmi, logging, socket, uuid
import win32com.client as client
from monitor_plugin import *
plugin_info("hostinfo.json")

'''
操作系统
cpu名字
cpu速度
磁盘容量
内存大小
计算机名
IP
mac
'''

win = wmi.WMI(moniker = "//./root/cimv2")
cim = client.GetObject("winmgmts:\\root\cimv2")
refresher = client.Dispatch("WbemScripting.SWbemRefresher")

win_os = win.Win32_OperatingSystem()[0]
win_cs = win.Win32_ComputerSystem()[0]
win_disk = win.Win32_DiskDrive()
win_ld = win.Win32_LogicalDisk()
win_cpu = win.Win32_Processor()
win_mem = win.Win32_PhysicalMemory()
win_nic = win.Win32_NetworkAdapterConfiguration()

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
iplist = socket.gethostbyname_ex(hostname)[2]

cpu_list = []
mem_list = []
nic_list = []

for cpu in win_cpu:
    cpu_list.append(dict(caption=cpu.Name, MaxClockSpeed=cpu.MaxClockSpeed,
                         NumberOfCores=cpu.NumberOfCores, NumberOfLogicalProcessors=cpu.NumberOfLogicalProcessors))
for mem in win_mem:
    mem_list.append(dict(Name=mem.DeviceLocator, Capacity=mem.Capacity))
    
for nic in win_nic:
    nic_list.append(dict(
        has_ip = nic.IPEnabled, 
        caption = nic.Description, 
        mac = nic.MACAddress, 
        subnet_mask = nic.IPSubnet,
        gateway = nic.DefaultIPGateway,
    ))
    
nc = sum(map(lambda x: x["NumberOfCores"], cpu_list))
nlp = sum(map(lambda x: x["NumberOfLogicalProcessors"], cpu_list))
cap = sum(map(lambda x: int(x["Capacity"]), mem_list))

result = dict(
    os          = win_os.Caption + " " + win_os.OSArchitecture, 
    serial      = win_os.SerialNumber,
    cpu         = cpu_list,
    number_of_cores = nc,
    number_of_logical_processors = nlp,
    mem         = mem_list,
    mem_capacity= cap,
    mac         = uuid.UUID(int = uuid.getnode()).hex[-12:],
    hostname    = hostname,
    ip          = iplist,
    nic         = nic_list
    )

print result
