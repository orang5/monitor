# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.contrib import auth
from datetime import datetime
from common.models import *
from common.agent_utils import *
from common import agent_utils, agent_info, mq, config
from common.agent_types import *
from django.contrib.auth.models import User
from form import RegisterForm,LoginForm
from models import *
from agent_utils import *
import json,random,time
import commandbroker, projectroot
from web.conf.Vchart import vc

def index(request):
    return render_to_response('index.html')

def index_update(request):
    
    d1 = [58, 28, 30, 69, 16, 37, 40]
    d2 = [28, 48, 40, 19, 86, 27, 90]
    data = dict(data1=d1, data2=d2)
    return HttpResponse(json.dumps(data))

def vplatform(request):
    return render_to_response('Vplatform.html')

def network(request):
    return render_to_response('Network.html')

def query_did(vmid):
    qc = CurrentModel.objects(uuid=vmid)
    devid = []        
    for q in qc:
        try:
            if not q.inst:
                try:
								    devid.append(q.DeviceID)
                except:
										pass
            else:
						    pass
        except:
            try:
								devid.append(q.DeviceID)
            except:
								pass			    
    devid = list(set(devid))                    
    return devid

def query_vminfo(vmid):
    query = CurrentInfoModel.objects(uuid=vmid)
    cap = CurrentModel.objects(uuid=vmid, name="mem_Capacity")
    capacity = 0

    for c in cap:
        capacity += int(c.value)
    vmInfo = {}
    for q in query:
        key = q.display_name
        if(key=="host_info"):
            temp = from_json(q.value)
            for mem in temp["mem"]:
                mem["Capacity"] = capacity
            niclist = []
            for nic in temp["nic"]:
                if nic["has_ip"]:
                    niclist.append(nic)
            temp["nic"] = niclist
            vmInfo[key] = temp
        elif(key == "installed_programs"):
            if len(q.value) > 8:
                temp = q.value[1:9]
            else:
                temp = q.value
            vmInfo[key] = temp
        else:
            vmInfo[key] = vmInfo.get(key,q.value)
    return vmInfo
    
def query_log(uuid=None):
    collection = None
    if uuid:
        collection = MetricModel.objects(name__startswith="Vim25Api", uuid=uuid)
    else:
        collection = MetricModel.objects(name__startswith="Vim25Api")
    ret = {}
    for evt in collection:
        ret[evt.key] = json.loads(evt.to_json())
    return ret.values()
    
def query_vmlist(host_uuid=None):
    if not host_uuid:
    # all
    # query entity_list in CurrentInfoModel
    # only one entry.
        host = {}
        for q in CurrentInfoModel.objects(name="entity_list"):
            for item in q.value:
                if item["mo_type"] == "HostSystem":
                    host[item["uuid"]] = item
                    
        # query vm_list in CurrentModel
        # one entry for each host.
        vmlist = {}
        for q in CurrentModel.objects(name="vm_list"):
            if q.uuid:
                vmlist[q.uuid] = q.value

        # return values
        for uuid in host.keys():
            host[uuid]["vm"] = vmlist[uuid]
            
        return host.values()
    
    else:
      # query vm_list in CurrentModel
      # one entry for each host.
      for q in CurrentModel.objects(name="vm_list", uuid=host_uuid):
          return q.value    
          
# get entity list in sidebar js
def vm_list(request):
    return HttpResponse(json.dumps(query_vmlist())) 
"""
def Host_static(request):
    try:
        vm_id = request.GET.get('uuid')
    except:
        vm_id = request
    ret = {'vmInfo':query_vminfo(vm_id), 'vmList' : query_vmlist(vm_id),
           'event':query_log(vm_id)}
    print ret
    return render_to_response('host.html', ret)
"""    
def Host(request):
    try:
        vm_id = request.GET.get('uuid')
    except:
        vm_id = request      
    charts = vc["charts"]
    did = query_did(vm_id)
    for ch in charts:
		    tag = ch["tag"]
		    r = []
		    for id in did:
		        if tag in id:
		            r.append(id)
		    ch["did"] = r
    ret = {'vmInfo':query_vminfo(vm_id), 'vmList' : query_vmlist(vm_id),
           'event':query_log(vm_id),"charts":charts}
    return render_to_response('host.html', ret)
        
def eventLog(request):
    try:
        id = request.GET.get('uuid')
    except:
        id = None
    return HttpResponse(json.dumps(query_log(id)))    
    
def virtualMachine(request):
		try:
				vm_id = request.GET.get('uuid')
		except:
				vm_id = request
		vmInfo = query_vminfo(vm_id)
		charts = vc["charts"]
		did = query_did(vm_id)
		for ch in charts:
		    tag = ch["tag"]
		    ret = []
		    for id in did:
		        if tag in id:
		            ret.append(id)
		    ch["did"] = ret
		return render_to_response('VirtualMachine.html' , {'vmInfo':vmInfo,'charts':charts})

def virtualMachine_update(request):
    try:
        vm_id = request.GET.get('uuid')
        DeviceId = request.GET.get('DeviceId')
        tag = request.GET.get("tag") 
    except:
        vm_id = request["uuid"]
        DeviceId = request["DeviceId"]
        tag = request["tag"]
        
    datasets = CurrentModel.objects(uuid = vm_id,DeviceID = DeviceId)
    points = []
    for ch in vc["charts"]:
        if tag == ch["tag"]:
            points = ch["points"]
    ret = []
    #old
    #for p in points:
    #    for data in datasets:
    #        if data.name in p["value"]:
    #            ret.append(data.value)
    #            continue
    #new
    #-1 represent no data
    for i,p in enumerate(points):
        ret.append(-1)
        for data in datasets:
            if data.name in p["value"]:
                ret[i]=data.value
                continue
      
               
    '''
    capacity = CurrentModel.objects(uuid = vm_id,DeviceID = "Physical_Memory_0")
    info = {"vmid" : vm_id, "dev" : DeviceId}
    for data in datasets:
        info[data.name] = data.value
    for data in capacity:
        info[data.name] = data.value
    # print request, info
    '''
    
    return HttpResponse(json.dumps(ret))   
    


def login(request):
    error=''
    if request.method == 'POST':
        form=LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
        
            user = auth.authenticate(username=username,password=password)
            if user and user.is_active:
                auth.login(request,user)
               
                return HttpResponseRedirect('index')
            else:
                error='The username does not exist or the password is wrong '
        else:
            error='your input is invalid'
               
    return render_to_response('login.html',{'error':error})
    

def register(request):
    error=''
    if request.method == 'POST':
        form=RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email=form.cleaned_data['email']
            password = form.cleaned_data['password']
            password2=form.cleaned_data['password2']
            if not User.objects.all().filter(username=username):
                if form.pwd_validate(password,password2):
                    user=User.objects.create_user(username,email,password)
                    user.save()
                   
                    return render_to_response('login.html')
                else:
                    error="Please input the same password"
                   
            else:
                error="The username has existed,please change you username" 
               
        else:
            error="The email is invalid,please change your email"       
    return render_to_response('register.html',{'error':error})
       
def usersManager(request):
    return render_to_response('users.html')
    
def management(request):
    return render_to_response('Management.html')
    
def management_update(request):
    status = request.GET.get('Status')
    ret = []
    vm_list = query_vmlist();
    for host in vm_list:
        vl = host["vm"]
        for vm in vl:
            if (vm['is_template'] == 'False' and vm['power'] == status):
                vm["host"] = host["mo"]
                ret.append(vm)
    return  HttpResponse(json.dumps(ret))

def init_jid():
    jobs = CurrentModel.objects(name="job_result")
    m = 0
    if jobs:
        for job in jobs:
            id = int(job.job_id)
            if m < id:
                m = id
    return m 

jid_impl = init_jid()

def retrieval_jid():
    global jid_impl
    jid_impl = jid_impl + 1
    return str(jid_impl)

def _control(**args):
    id = config.vsphere_id
    ip = config.vsphere_agent
    q = mq.connect_control(id, "remote", ip, lambda x:"do not block")
    time.sleep(1)
    req = dict(op="plugin_info",uuid=id)
    datasets = CurrentModel.objects(name="agent_plugin_list",uuid=id)
    plugin_info = dict()
    for d in datasets:
        plugin_info = d.value
    req = dict(**args)
    req["uuid"] = id
    req["pid"] = plugin_info["monitor_vsphere"]["pid"]
    mq.request(agent_utils.to_json(req), id)
    q.close();

    
def vmControl(request):
    try:
        operation = request.GET.get("op")
        vm_uuid = request.GET.get("vm_uuid")
        vm_name = request.GET.get("vmName")
    except:
        operation = request["op"]
        vm_uuid = request["vm_uuid"]
        vm_name = request["vmName"]          
    jid = retrieval_jid()
    req = dict(op=operation,job_id=jid, name=vm_name, vmid=vm_uuid) 
    _control(**req)
    perf = dict(name=vm_name,job_id=jid)
    return HttpResponse(json.dumps(perf))
    
#tofix
Status = dict(poweron="poweredOn", poweroff="poweredOff", suspend="suspended", reboot="poweredOn")
    
def fetch_perf(request):
      
    try:
        vm_name = request.GET.get("vmName")
        jid = request.GET.get("jid")
    except:
        vm_name = request["vmName"]
        jid = request["jid"]
    objs = CurrentModel.objects(name="job_result",job_id=jid)
    perf = dict()
    if objs:
        for obj in objs:
            if obj.value["result"]:
                perf = dict(is_co=1, status=Status[obj.value["op"]])
    else:
         perf = dict(is_co=0, status="error")  
    return HttpResponse(json.dumps(perf))
    
    
if __name__ == '__main__':
    #req = dict(op="poweroff",jod_id=0, name="master0.islab.org", vmid='0050568b6c03') 
    #_control(**req)
    print jid_impl
    for i in range(10):
        id = retrieval_jid()
        print id
    '''
    vm_id = "0050568b044b"
    #print virtualMachine_test("0050568b47dd","","net")
    vmlist = query_vmlist()
    for vms in vmlist:
        for k,v in vms.items():
            print k,v
            print "======================"
        print "--------------------------"    
            
    #print query_vmlist()
    #print query_vmlist("00e081e21135")
    # Host_static(vm_id)
    #for i in range(4):
        #v = query_vminfo(vm_id)
        #for d in v["devs"]:
            #print d
    # print virtualMachine_static(vm_id)
    # print virtualMachine_update({"uuid":vm_id, "DeviceId":"SysMemory"})
    #print query_log()
    #print query_did(vm_id, 'disk')
    #print vc
    objs = CurrentModel.objects(name="job_result",job_id=1)
    perf = dict()
    if not objs:
        print "nothing"
    for obj in objs:
        print obj
        perf = dict(is_co=1, status=obj.value["name"])
    print perf
    '''