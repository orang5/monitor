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
        perf["cpu"] = perf.get("cpu", {"snapshot" : None, "ts" : ts, "perfos" : None})
        snapshot = perf["cpu"]["snapshot"]
        snap_ts = perf["cpu"]["ts"]
        snap_perf = perf["cpu"]["perfos"]
        
        if (not snapshot) or ts>snap_ts + 1:
            perf["cpu"]["snapshot"] = snapshot = win.wmi.Win32_Processor()
            perf["cpu"]["ts"] = snap_ts = time.time()
            perf["cpu"]["perfos"] = snap_perf = win.wmi.Win32_PerfRawData_PerfOS_Processor()
            
        if met.name == "cpu_LoadPercentage":
            # use perfrawdata class instead.
            for i in xrange(0, len(snap_perf)):
                perf["cpu"][i] = perf["cpu"].get(i, { "count" : int(snap_perf[i].PercentIdleTime), "ts" : 0 })
                raw = snap_perf[i]
                count = int(raw.PercentIdleTime)
                ts = int(raw.TimeStamp_Sys100NS)
                # print count, ts
                if ts > perf["cpu"][i]["ts"]:
                    met.value = 100 - 100 * (count - perf["cpu"][i]["count"]) / (ts - perf["cpu"][i]["ts"])
                    perf["cpu"][i]["count"] = count
                    perf["cpu"][i]["ts"] = ts                    
                    
                    met.tags["DeviceID"] = "id__cpu_" + raw.Name
                    met.ts["latest"] = snap_ts
                    publish(met)
        else:
            for i,cpu in enumerate(snapshot):
                met.value = cpu.__getattr__(names[1])
                met.tags["DeviceID"] = "id__cpu_" + str(i)
                met.tags["tag"] = "id__cpu_" + str(i)
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
                met.tags["DeviceID"] = "mem__" + mm.Tag.replace(' ','_')           
                publish(met)        
        else:
            os = win.wmi.Win32_OperatingSystem()
            pfu = win.wmi.Win32_PageFileUsage()  

            info_dict['mem_Free'] =  float(os[0].FreePhysicalMemory) / 1024     # 'unit':'MB'}
            info_dict['mem_SwapTotal'] = float(pfu[0].AllocatedBaseSize)        # 'unit':'MB'}
            info_dict['mem_SwapUsage'] = float(pfu[0].CurrentUsage)             #   'unit':'MB'}
            info_dict["mem_SwapFree"] = float(pfu[0].AllocatedBaseSize - pfu[0].CurrentUsage) # 'unit':'MB'}
            met.value = info_dict[met.name]
            met.tags["DeviceID"] = 'mem__sys'
            publish(met)     
            
    elif names[0] == "disk":
        if names[1] == "size":
            for physical_disk in win.wmi.Win32_DiskDrive():
                met.value = round(float(physical_disk.Size) / (1024*1024*1024), 2) # 'unit':'GB'}
                met.tags["tag"] = physical_disk.Caption
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
                met.tags["tag"] = item.Name
                met.tags["DeviceID"] = "disk__" + item.Name
                publish(met)
            win.com.DeleteAll()
        else:
            #  DriveType=3 : "Local Disk",
            for disk in win.wmi.Win32_LogicalDisk(DriveType=3):
                info_dict = {}
                info_dict['disk_FreeSpace'] =  round(float(disk.FreeSpace) / (1024*1024*1024), 2)       # 'unit':'GB'}
                info_dict['disk_capacity'] =  round(float(disk.Size) / (1024*1024*1024), 2)             # 'unit':'GB'}
                info_dict['disk_Used'] = round((float(disk.Size)-float(disk.FreeSpace)) / (1024*1024*1024), 2) # 'unit':'GB'}
                info_dict['disk_fstype'] = disk.FileSystem
                
                met.value = info_dict[met.name]
                met.tags["tag"] = disk.DeviceID
                met.tags["DeviceID"] = "disk__" + disk.DeviceID
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
                    met.tags["tag"] = interface.Description               
                publish(met)
        else:     
            items = win.com.AddEnum(win.obj, "Win32_PerfRawData_Tcpip_NetworkInterface").objectSet
            win.com.Refresh() 
            for item in items:
                met.tags = {}
                # internal routine: update net perf aggregated values
                ts = int(item.Timestamp_PerfTime)
                base = int(item.Frequency_PerfTime)  # cpu frequency as divisor
                net_bytes[item.Name] = net_bytes.get(item.Name,
                    {"in":long(item.BytesReceivedPerSec), "out":long(item.BytesSentPerSec), "s_in":0, "s_out":0, "ts":ts})
                it = net_bytes[item.Name]                
                dt = ts - it["ts"]

                net_dict["net_bytes_in_cur"]  = br = long(item.BytesReceivedPerSec)
                net_dict["net_bytes_out_cur"] = bs = long(item.BytesSentPerSec)
                net_dict['net_pkts_in_cur'] = long(item.PacketsReceivedPerSec)
                net_dict['net_pkts_out_cur'] = long(item.PacketsSentPerSec)
                
                if dt > base:   # need refresh
                    # count speed
                    it["s_in"] = (br-it["in"]) / (float(dt*1024)/base)           # 'unit':'Kbps'}
                    it["s_out"] = (bs-it["out"]) / (float(dt*1024)/base)         # 'unit':'Kbps'}
                    
                  #  print item.name, "dt", float(dt)/base, "in", br-it["in"], "out", bs-it["out"], it["s_in"], it["s_out"]
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
                    met.tags["tag"] = item.Name
                met.tags["DeviceID"] = "net__" + item.Name.replace(' ','_')
            
                publish(met)

                
            win.com.DeleteAll()
    #need no more               
    elif names[0] == "dev":
        if names[1] == "cpu":
            for cpu in win.wmi.Win32_Processor():
                met.tags['DeviceID'] = cpu.DeviceID
                met.value = dict(index = cpu.DeviceID, caption = cpu.Name)
                publish(met)
        elif names[1] == "disk":
            for i,disk in enumerate(win.wmi.Win32_LogicalDisk (DriveType=3)):
                met.tags['DeviceID'] = 'disk__' + disk.DeviceID
                met.value = dict(index = i, caption = disk.DeviceID)
                publish(met)
        elif names[1] == "nic":                
            for i,interface in enumerate(win.wmi.Win32_NetworkAdapterConfiguration (IPEnabled=1)):
                met.tags = {}
                met.tags['DeviceID'] = "net__" + interface.Description.replace(' ','_')
                if interface.MACAddress:
                    met.value = dict(mac=format_mac(interface.MACAddress), caption=interface.Description, index=i) 
                    met.tags['mac'] = format_mac(interface.MACAddress)
                    publish(met)
                    if not net_bytes.has_key(interface.Description): net_bytes[interface.Description] = met.value
        elif names[1] == "mem":  
            cp = win.wmi.Win32_PhysicalMemory()
            for mm in cp:
                met.tags['tag'] = mm.Tag
                met.tags["DeviceID"] = "mem__" + mm.Tag.replace(' ','_')
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
    log.info("[WinWatcher] 连接 WMI...")
    win = WinWatcher()
    win.init_wmi()
    log.info("[WinWatcher] 开始收集数据...")
    while flag:
        update_metrics(metric_worker, publish=False)
        time.sleep(0.3)

if __name__ == '__main__': do_work()
