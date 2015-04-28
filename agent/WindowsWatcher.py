import time,pythoncom, wmi
import win32com.client as client
from watcher import Watcher
con = None
class _wmi_ctx(object):
    def __enter__(self):
        global con
        try:
            con = wmi.WMI()
            self.should_unInit = False
            con = None
        except:
            pythoncom.CoInitialize()
            self.should_unInit = True
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

class WinWatcher(Watcher):
    def __init__(self):
        super(WinWatcher, self).__init__()
    
    @with_wmi
    def sys_version(self):       
        for sys in con.Win32_OperatingSystem(): 
            print "Version:%s" % sys.Caption,"Vernum:%s" % sys.BuildNumber 
            print 'OS Architecture: %s' % sys.OSArchitecture
     
    @with_wmi 
    def cpu_use(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        cpu_info = []
        cpu_dict = {}
        for cpu in con.Win32_Processor():          
            info_dict = {}
            info_dict['cpu_LoadPercentage'] =  {'volume':cpu.LoadPercentage , 'unit':'%'}
            info_dict['cpu_CurrentClockSpeed'] = {'volume':cpu.CurrentClockSpeed , 'unit':'MHZ'}
            info_dict['cpu_NumberOfCores'] = cpu.NumberOfCores
            info_dict['cpu_MaxClockSpeed'] = {'volume':cpu.MaxClockSpeed , 'unit':'MHZ'}
            info_dict['cpu_NumberOfLogicalProcessors'] = cpu.NumberOfLogicalProcessors
            info_dict['cpu_Description'] = cpu.Description
            info_dict['cpu_Name'] = cpu.Name
            cpu_dict[cpu.DeviceID] = info_dict
            cpu_info.append(cpu_dict)
        return cpu_info   
            
    @with_wmi                           
    def mem_use(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        mem_info = []
        mem_dict = {}
        info_dict = {}
        cp = con.Win32_PhysicalMemory()
        #cs = c.Win32_ComputerSystem()   
        os = con.Win32_OperatingSystem()
        pfu = con.Win32_PageFileUsage()  
        info_dict['mem_Capacity'] =  {'volume':float(cp[0].Capacity) / (1024*1024) , 'unit':'MB'}
        info_dict['mem_Free'] =  {'volume':float(os[0].FreePhysicalMemory) / 1024 , 'unit':'MB'}
        info_dict['mem_SwapTotal'] =  {'volume':float(pfu[0].AllocatedBaseSize) , 'unit':'MB'}
        info_dict['mem_SwapUsage'] =  {'volume':float(pfu[0].CurrentUsage) , 'unit':'MB'}
        info_dict["mem_SwapFree"] = {'volume':float(pfu[0].AllocatedBaseSize - pfu[0].CurrentUsage) , 'unit':'MB'}
        info_dict['mem_Speed'] =  {'volume':cp[0].Speed , 'unit':'MHZ'}
        info_dict['mem_DeviceLocator'] = cp[0].DeviceLocator
        mem_dict[cp[0].Tag] = info_dict
        mem_info.append(mem_dict)
        return mem_info
        
    @with_wmi              
    def get_fs_info(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        disk_info = []
        disk_dict = {}
        info_dict = {}
        #  DriveType=3 : "Local Disk",
        for disk in con.Win32_LogicalDisk (DriveType=3):
            info_dict = {}
            info_dict['disk_FreeSpace'] =  {'volume':round(float(disk.FreeSpace) / (1024*1024*1024), 2) , 'unit':'GB'}
            info_dict['disk_capacity'] =  {'volume':round(float(disk.Size) / (1024*1024*1024), 2) , 'unit':'GB'}
            info_dict['disk_Used'] = {'volume':round((float(disk.Size)-float(disk.FreeSpace)) / (1024*1024*1024), 2) , 'unit':'GB'}
            info_dict['fstype'] = disk.FileSystem
            info_dict['mnt'] = ''
            #print disk.DeviceID
            disk_dict[disk.DeviceID] = info_dict

        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        diskitems = com.AddEnum(obj, "Win32_PerfFormattedData_PerfDisk_LogicalDisk").objectSet
        
        com.Refresh()
        for item in diskitems:
            try:
                disk_dict[item.Name]['io_stat_read'] = {'volume':(float(item.DiskReadBytesPerSec) / 1024), 'unit':'KB/s'}
                disk_dict[item.Name]['io_stat_write'] = {'volume':(float(item.DiskWriteBytesPerSec) / 1024), 'unit':'KB/s'}
            except:
                pass
            disk_info.append(disk_dict)
        return disk_info
    
    @with_wmi
    def get_disk_info(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        disk_info = []
        disk_dict = {}
        for physical_disk in con.Win32_DiskDrive ():
            info_dict = {}
            info_dict["Size"] = {'volume':round(float(physical_disk.Size) / (1024*1024*1024), 2) , 'unit':'GB'}
            disk_dict[physical_disk.Caption] = info_dict
            disk_info.append(disk_dict)
        return disk_info
    
    @with_wmi
    def network(self):
        con = wmi.WMI(moniker = "//./root/cimv2")
        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        items = com.AddEnum(obj, "Win32_PerfRawData_Tcpip_NetworkInterface").objectSet
        net_info = []
        net_dict = {}
        for interface in con.Win32_NetworkAdapterConfiguration (IPEnabled=1):
            info_dict = {}
            info_dict['net_MACAddress'] = interface.MACAddress
            info_dict['net_IPSubnet'] = interface.IPSubnet
            info_dict['net_DefaultIPGateway'] = interface.DefaultIPGateway
            info_dict['net_ip_address'] = []
            for ip_address in interface.IPAddress:
                info_dict['net_ip_address'].append(ip_address)
            net_dict[interface.Description] = info_dict
             
        
        com.Refresh()
        for item in items:
            if net_dict.has_key(item.Name):
                net_bytes_in = long(item.BytesReceivedPerSec)
                net_bytes_out = long(item.BytesSentPerSec)
                    
                time.sleep(1)
                com.Refresh()

                net_dict[item.Name]['net_bytes_in'] = {'volume':(long(item.BytesReceivedPerSec) - net_bytes_in)*8/1024 , 'unit':'Kbps'}
                net_dict[item.Name]['net_bytes_out'] = {'volume':(long(item.BytesSentPerSec) - net_bytes_out)*8/1024 , 'unit':'Kbps'}
                net_dict[item.Name]['net_bytes_in_cur'] = {'volume':long(item.BytesReceivedPerSec) , 'unit':'B'}
                net_dict[item.Name]['net_bytes_in_cur'] = {'volume':long(item.BytesReceivedPerSec) , 'unit':'B'}
                net_dict[item.Name]['net_pkts_in_cur'] = long(item.PacketsReceivedPerSec)
                net_dict[item.Name]['net_pkts_out_cur'] = long(item.PacketsSentPerSec)
                net_info.append(net_dict)
        return net_info
    
    @with_wmi    
    def current_process(self):         
        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        items = com.AddEnum(obj, "Win32_PerfFormattedData_PerfProc_Process").objectSet
        com.Refresh()
        for item in items:
            timestamp = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            print item.IDProcess, item.Name, item.PriorityBase, item.VirtualBytes, item.PoolNonpagedBytes, item.PoolPagedBytes, item.PercentProcessorTime, item.WorkingSet, timestamp    
     
    @with_wmi    
    def static(self):
        '''
        sys_version
        cpu_data['MaxClockSpeed'] = cpu.MaxClockSpeed
        cpu_data['NumberOfCores'] = cpu.NumberOfCores
        cpi_data['NumberOfLogicalProcessors'] = cpu.NumberOfLogicalProcessors
        '''
        pass
        
            
if __name__ == '__main__': 
    win = WinWatcher()
    print '--------cpu------------------------------------------'
    print win.cpu_use()
    print '--------memory---------------------------------------'
    print win.mem_use()
    print '--------fs_info-----------------------------------------'
    print win.get_fs_info()
    print '--------dsik_info-----------------------------------------'
    print win.get_disk_info()    
    print '--------network--------------------------------------'
    print win.network()

    '''
    while True:
        data = win.get_fs_info()
        print data
        print '-------current process-----------------------------'
        win.current_process()        
    '''