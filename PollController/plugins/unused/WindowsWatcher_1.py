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
        
#    @with_wmi
    def sys_version(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        for sys in con.Win32_OperatingSystem():
            for k in sys.properties:
                print getattr(sys, k)
            #print "Version:%s" % sys.Caption,"Vernum:%s" % sys.BuildNumber 
            #print 'OS Architecture: %s' % sys.OSArchitecture

   # @with_wmi    
    def current_process(self):         
        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        items = com.AddEnum(obj, "Win32_PerfFormattedData_PerfProc_Process").objectSet
        com.Refresh()
        for item in items:
            timestamp = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            print item.IDProcess, item.Name, item.PriorityBase, item.VirtualBytes, item.PoolNonpagedBytes, item.PoolPagedBytes, item.PercentProcessorTime, item.WorkingSet, timestamp    
     
def metric_worker(met):
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
        os = win.wmi.Win32_OperatingSystem()
        pfu = win.wmi.Win32_PageFileUsage()  
        info_dict['mem_Capacity'] =  float(cp[0].Capacity) / (1024*1024)    # 'unit':'MB'}
        info_dict['mem_Free'] =  float(os[0].FreePhysicalMemory) / 1024     # 'unit':'MB'}
        info_dict['mem_SwapTotal'] = float(pfu[0].AllocatedBaseSize)        # 'unit':'MB'}
        info_dict['mem_SwapUsage'] = float(pfu[0].CurrentUsage)             #   'unit':'MB'}
        info_dict["mem_SwapFree"] = float(pfu[0].AllocatedBaseSize - pfu[0].CurrentUsage) # 'unit':'MB'}
        info_dict['mem_Speed'] =  cp[0].Speed       # 'unit':'MHZ'}
        info_dict['mem_DeviceLocator'] = cp[0].DeviceLocator
        
        met.value = info_dict[met.name]
        met.tags["tag"] = cp[0].Tag
        publish(met)        

    elif names[0] == "disk":
        if names[1] == "size":
            for physical_disk in win.wmi.Win32_DiskDrive():
                met.value = round(float(physical_disk.Size) / (1024*1024*1024), 2) # 'unit':'GB'}
                met.tags["Caption"] = physical_disk.Caption
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
                met.tags["item_name"] = item.Name
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
                met.tags["DeviceID"] = disk.DeviceID
                met.tags["index"] = i
                publish(met)
                
    elif names[0] == "net":
        if met.type == "config":
            net_info = []
            net_dict = {}
            net_id_disk = {}
            for i,interface in enumerate(win.wmi.Win32_NetworkAdapterConfiguration (IPEnabled=1)):
                info_dict = {}
                info_dict['net_MACAddress'] = interface.MACAddress
                info_dict['net_IPSubnet'] = interface.IPSubnet
                info_dict['net_DefaultIPGateway'] = interface.DefaultIPGateway
                info_dict['net_ip_address'] = []
                info_dict['Caption'] = interface.Description
                if not interface.IPAddress is None:
                    for ip_address in interface.IPAddress:
                        info_dict['net_ip_address'].append(ip_address)
                        
                met.value = info_dict[met.name]
                met.tags["Caption"] = interface.Description
                met.tags["index"] = i
                publish(met)
        else:     
            global net_bytes
            net_dict = {}
            items = win.com.AddEnum(win.obj, "Win32_PerfRawData_Tcpip_NetworkInterface").objectSet
            win.com.Refresh()            
            for item in items:
                # internal routine: update net perf aggregated values
                ts = time.time()
                if not net_bytes.has_key(item.Name):
                    net_bytes[item.Name] = {"in" : long(item.BytesReceivedPerSec), "out" : long(item.BytesSentPerSec),
                                       "s_in" : 0, "s_out" : 0, "ts" : ts}                     
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
                met.tags["item_name"] = item.Name
                publish(met)
                
            win.com.DeleteAll()
                   
    elif names[0] == "dev":
        result = []
        if names[1] == "cpu":
            for cpu in win.wmi.Win32_Processor():
                result.append({'caption':cpu.Name,'index':cpu.DeviceID})
        elif names[1] == "disk":
            for i,disk in enumerate(win.wmi.Win32_LogicalDisk (DriveType=3)):
                result.append({'caption':disk.DeviceID,'index':i})
        elif names[1] == "nic":                
            for i,interface in enumerate(win.wmi.Win32_NetworkAdapterConfiguration (IPEnabled=1)):
                result.append({'caption':interface.Description,'index':i})   
        elif names[1] == "mem":  
            cp = win.wmi.Win32_PhysicalMemory()
            result.append({'caption':cp[0].Tag,'index':0})
        
        met.value = result
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
