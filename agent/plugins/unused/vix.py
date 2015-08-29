import win32com.client as client
import win32com.server.register as register
import win32com.server.policy as policy
import time

cc = client.constants
vix = client.Dispatch("VixCOM.VixLib")
mod = client.gencache.GetModuleForProgID("VixCOM.VixLib")

class PyCom_SearchCallback(mod.ICallback):
    def OnVixEvent(self, job, type, more_info):
        if type == cc.VIX_EVENTTYPE_FIND_ITEM:
            ret = None
            err, ret = more_info.GetProperties([cc.VIX_PROPERTY_FOUND_ITEM_LOCATION], ret)
            if err==0:
                print ret[0]
            else:
                print err[0], err[1]

ret = []
job = vix.Connect(cc.VIX_API_VERSION, cc.VIX_SERVICEPROVIDER_VMWARE_WORKSTATION, None, 0, None, None, 0, None, None)
err, ret = job.Wait([cc.VIX_PROPERTY_JOB_RESULT_HANDLE], ret)
print vix
print job
print err, ret
if err==0:
    # success
    host = ret[0]
    job = host.FindItems(cc.VIX_FIND_REGISTERED_VMS, None, -1, PyCom_SearchCallback())
    job.WaitWithoutResults()
    
    host.Disconnect()