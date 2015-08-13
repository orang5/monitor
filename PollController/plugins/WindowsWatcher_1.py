# -*- coding: utf-8 -*-
import time,pythoncom, wmi, logging
import win32com.client as client
from monitor_plugin import *
plugin_info("WindowsWatcher_1.json")

interval = 30
flag = True
win = None
net_bytes = {}
perf = {}

# init COM environment in multi-thread context, which supports WMI.
# does not init WMI by this decorator.
class _wmi_ctx(object):
    def __enter__(self):
        try:
            pythoncom.CoInitialize()
            self.should_unInit = True
        except:
            logging.info('Running in single thread!')
            pass
        return self
    
    def __exit__(self, exctype, excvalue, traceback):
        if self.should_unInit:    
            pythoncom.CoUninitialize()
            
def _with_wmi_ctx():
    return _wmi_ctx()

def with_wmi(func):
    def _wrapper(*args, **kw):
        with _with_wmi_ctx():
            return func(*args, **kw)
    return _wrapper        

class WinWatcher(object):

#    @with_wmi
    def init_wmi(self):
        self.wmi = wmi.WMI(moniker = "//./root/cimv2")
        self.obj = client.GetObject("winmgmts:\\root\cimv2")
        self.com = client.Dispatch("WbemScripting.SWbemRefresher")
        
def format_mac(mac):
    return "".join(mac.split(":")).lower()

def metric_worker(met):
    global net_bytes
    names = met.name.split("_", 1)
    if names[0] == "cpu":
        global perf
        ts = time.time()
        perf["cpu"] = perf.get("cpu", {"snapshot" : None, "ts" : ts})
        snapshot = perf["cpu"]["snapshot"]
        snap_ts = perf["cpu"]["ts"]
        
        if (not snapshot) or ts>snap_ts+met.interval:
            perf["cpu"]["snapshot"] = snapshot = win.wmi.Win32_Processor()
            perf["cpu"]["ts"] = snap_ts = time.time()
            
        for cpu in snapshot:
            met.value = cpu.__getattr__(names[1])
            met.tags["DeviceID"] = cpu.DeviceID
            met.ts["latest"] = snap_ts
            publish(met)
            
    elif names[0] == "mem":
        info_dict = {}
        cp = win.wmi.Win32_PhysicalMemory()
        
        if met.name == "mem_Capacity" or met.name == "mem_Speed" or met.name == "mem_DeviceLocator":
            for mm in cp:
                info_dict['mem_Capacity'] =  float(mm.Capacity) / (1024*1024)    # 'unit':'MB'}
                info_dict['mem_Speed'] =  mm.Speed       # 'unit':'MHZ'}
                info_dict['mem_DeviceLocator'] = mm.DeviceLocator
                met.value = info_dict[met.name]
                met.tags["tag"] = mm.Tag
                publish(met)        
        else:
            os = win.wmi.Win32_OperatingSystem()
            pfu = win.wmi.Win32_PageFileUsage()  

            info_dict['mem_Free'] =  float(os[0].FreePhysicalMemory) / 1024     # 'unit':'MB'}
            info_dict['mem_SwapTotal'] = float(pfu[0].AllocatedBaseSize)        # 'unit':'MB'}
            info_dict['mem_SwapUsage'] = float(pfu[0].CurrentUsage)             #   'unit':'MB'}
            info_dict["mem_SwapFree"] = float(pfu[0].AllocatedBaseSize - pfu[0].CurrentUsage) # 'unit':'MB'}
            met.value = info_dict[met.name]
            publish(met)     
            
    elif names[0] == "disk":
        if names[1] == "size":
            for physical_disk in win.wmi.Win32_DiskDrive():
                met.value = round(float(physical_disk.Size) / (1024*1024*1024), 2) # 'unit':'GB'}
                met.tags["caption"] = physical_disk.Caption
                publish(met)
        elif names[1].startswith("io"):
            diskitems = win.com.AddEnum(win.obj, "Win32_PerfFormattedData_PerfDisk_LogicalDisk").objectSet
            win.com.Refresh()
            for item in diskitems:
                try:
                    disk_dict = {}
                    disk_dict['io_stat_read'] = float(item.DiskReadBytesPerSec) / 1024      #  'unit':'KB/s'}
                    disk_dict['io_stat_write'] = float(item.DiskWriteBytesPerSec) / 1024    # 'unit':'KB/s'}
                except: pass                
                met.value = disk_dict[names[1]]
                met.tags["caption"] = item.Name
                publish(met)
            win.com.DeleteAll()
        else:
            #  DriveType=3 : "Local Disk",
            for i,disk in enumerate(win.wmi.Win32_LogicalDisk(DriveType=3)):
                info_dict = {}
                info_dict['disk_FreeSpace'] =  round(float(disk.FreeSpace) / (1024*1024*1024), 2)       # 'unit':'GB'}
                info_dict['disk_capacity'] =  round(float(disk.Size) / (1024*1024*1024), 2)             # 'unit':'GB'}
                info_dict['disk_Used'] = round((float(disk.Size)-float(disk.FreeSpace)) / (1024*1024*1024), 2) # 'unit':'GB'}
                info_dict['disk_fstype'] = disk.FileSystem
                
                met.value = info_dict[met.name]
                met.tags["caption"] = disk.DeviceID
                met.tags["index"] = i
                publish(met)
                
    elif names[0] == "net":
        net_info = []
        net_dict = {}
        if met.type == "config":
            net_id_disk = {}
            for i,interface in enumerate(win.wmi.Win32_NetworkAdapterConfiguration (IPEnabled=1)):
                met.tags = {}
                info_dict = {}
                info_dict['net_MACAddress'] = interface.MACAddress
                info_dict['net_IPSubnet'] = interface.IPSubnet
                info_dict['net_DefaultIPGateway'] = interface.DefaultIPGateway
                info_dict['net_ip_address'] = []
                info_dict['net_Caption'] = interface.Description
                if not interface.IPAddress is None:
                    for ip_address in interface.IPAddress:
                        info_dict['net_ip_address'].append(ip_address)
                        
                met.value = info_dict[met.name]
                
                if net_bytes[interface.Description].has_key("mac"):
                    met.tags["mac"] = net_bytes[interface.Description]["mac"]
                else:
                    met.tags["caption"] = interface.Description

                met.tags["index"] = i
                publish(met)
        else:     
            items = win.com.AddEnum(win.obj, "Win32_PerfRawData_Tcpip_NetworkInterface").objectSet
            win.com.Refresh() 
            for item in items:
                met.tags = {}
                # internal routine: update net perf aggregated values
                ts = time.time()
                if not net_bytes.has_key(item.Name): net_bytes[item.Name] = {}
                net_bytes[item.Name].update({"in":long(item.BytesReceivedPerSec), "out":long(item.BytesSentPerSec),
                                            "s_in":0, "s_out":0, "ts":ts})                     
                it = net_bytes[item.Name]                
                dt = ts - it["ts"]

                net_dict["net_bytes_in_cur"]  = br = long(item.BytesReceivedPerSec)
                net_dict["net_bytes_out_cur"] = bs = long(item.BytesSentPerSec)
                net_dict['net_pkts_in_cur'] = long(item.PacketsReceivedPerSec)
                net_dict['net_pkts_out_cur'] = long(item.PacketsSentPerSec)
                
                if dt > 2:   # need refresh
                    # count speed
                    it["s_in"] = (br - it["in"])*8/(dt*1024)           # 'unit':'Kbps'}
                    it["s_out"] = (bs - it["out"])*8/(dt*1024)         # 'unit':'Kbps'}
                    # update in/out and timestamp
                    it["in"] = br
                    it["out"] = bs
                    it["ts"] = ts
         
                net_dict["net_bytes_in"] = it["s_in"]
                net_dict["net_bytes_out"] = it["s_out"]
                
                met.value = net_dict[met.name]
                
                if net_bytes[item.Name].has_key("mac"):
                    met.tags["mac"] = net_bytes[item.Name]["mac"]
                else:
                    met.tags["caption"] = item.Name
                publish(met)
                
            win.com.DeleteAll()
                   
    elif names[0] == "dev":
        if names[1] == "cpu":
            for cpu in win.wmi.Win32_Processor():
                met.tags['index'] = cpu.DeviceID
                met.value = dict(index = cpu.DeviceID, caption = cpu.Name)
                publish(met)
        elif names[1] == "disk":
            for i,disk in enumerate(win.wmi.Win32_LogicalDisk (DriveType=3)):
                met.tags['index'] = i
                met.value = dict(index = i, caption = disk.DeviceID)
                publish(met)
        elif names[1] == "nic":                
            for i,interface in enumerate(win.wmi.Win32_NetworkAdapterConfiguration ()):
                if interface.MACAddress:
                    met.tags = {}
                    met.tags['index'] = i
                    met.value = dict(mac=format_mac(interface.MACAddress), caption=interface.Description, index=i) 
                    met.tags['mac'] = format_mac(interface.MACAddress)
                    publish(met)
                    if not net_bytes.has_key(interface.Description): net_bytes[interface.Description] = met.value
        elif names[1] == "mem":  
            cp = win.wmi.Win32_PhysicalMemory()
            for mm in cp:
                met.tags['index'] = mm.Tag
                met.value = dict(index = mm.Tag, caption = mm.DeviceLocator)
                publish(met)
                
    elif met.name == "process_list":
        items = win.com.AddEnum(win.obj, "Win32_PerfFormattedData_PerfProc_Process").objectSet
        win.com.Refresh()
        met.value = []
        for item in items:
            met.value.append(dict(
                pid=item.IDProcess, name=item.Name, cpu=item.PercentProcessorTime, 
                elapsed=item.ElapsedTime, io=item.IODataBytesPerSec, mem=item.VirtualBytes))
        publish(met)
        win.com.DeleteAll()
            # print item.IDProcess, item.Name, item.PriorityBase, item.VirtualBytes, item.PoolNonpagedBytes, item.PoolPagedBytes, item.PercentProcessorTime, item.WorkingSet, timestamp
    
    elif met.name == "program_list":
        met.value = []
        for p in win.wmi.Win32_Product():
            met.value.append(dict(
                name=p.Caption, version=p.Version, description=p.Description, vendor=p.Vendor))
        publish(met)    
        
@with_wmi
def do_work():
    global win
    print "[WinWatcher] init WMI..."
    win = WinWatcher()
    win.init_wmi()
    print "[WinWatcher] start main loop..."
    while flag:
        update_metrics(metric_worker, publish=False)
        time.sleep(1)


if __name__ == '__main__': do_work()
