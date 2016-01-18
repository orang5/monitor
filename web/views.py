# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User,Permission
from django.contrib.auth.decorators import login_required,permission_required
from django.template.context import RequestContext
from form import RegisterForm,LoginForm
from common.agent_utils import *
from common import agent_utils, agent_info, mq, config
from common.agent_types import *
import commandbroker, projectroot
from views_query import *
from web.conf.vChart import vc
import json,random,time,datetime

log = agent_utils.getLogger()

@login_required(login_url='/accounts/login')
def index(request):
    return render_to_response('index.html',RequestContext(request))

def index_update(request):
    
    queryMetric.set(name = 's_vm_mem_consumed_sum', mo='dev')
    memSets = queryMetric.byHours(2)
    queryMetric.set(name = 's_host_cpu_usage_avg', mo='dev')
    cpuSets = queryMetric.byDays(2)
    (labels, s_cpu) = metric_filter(cpuSets, 60, formate['minute'])
    (labels, s_mem) = metric_filter(memSets, 60, formate['minute'])


    ret = dict(labels=labels, s_cpu=s_cpu, s_mem=s_mem)
    log.debug("response from index_update: %s" % ret)
    return HttpResponse(json.dumps(ret))

@login_required(login_url='/accounts/login')
def vplatform(request):
    return render_to_response('Vplatform.html',RequestContext(request))

@login_required(login_url='/accounts/login')
def network(request):
    return render_to_response('Network.html',RequestContext(request))
          
# get entity list in sidebar js
def vm_list(request):
    return HttpResponse(json.dumps(query_vmlist())) 
@login_required(login_url='/accounts/login')   
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
		    
    vm_list = query_vmlist(vm_id)
    events = query_log(vm_id)
    for vm in vm_list:
        events.extend(query_log(vm["uuid"]))
    ret = {'vmInfo':query_vminfo(vm_id), 'vmList' : vm_list,
           'event':events,"charts":charts}
    log.debug(r"render to host.html: %s" % ret)
    return render_to_response('host.html', ret,RequestContext(request))
        
def eventLog(request):
    try:
        id = request.GET.get('uuid')
    except:
        id = None
    ret = query_log(id)
    log.debug(r"response form eventLog: %s" % ret)
    return HttpResponse(json.dumps(ret))    
@login_required(login_url='/accounts/login')    
def virtualMachine(request):
		try:
				uuid = request.GET.get('uuid')
		except:
				uuid = request
		vmInfo = query_vminfo(uuid)
		charts = vc["charts"]
		did = query_did(uuid)
		for ch in charts:
		    tag = ch["tag"]
		    ret = []
		    for id in did:
		        if tag in id:
		            ret.append(id)
		    ch["did"] = ret
		log.debug(r"render to VirtualMachine.html: %s\n%s" % (vmInfo,charts))
		return render_to_response('VirtualMachine.html' , {'vmInfo':vmInfo,'charts':charts},RequestContext(request))

def virtualMachine_update(request):
    try:
        uuid = request.GET.get('uuid')
        DeviceID = request.GET.get('DeviceId')
        tag = request.GET.get("tag") 
    except:
        uuid = request["uuid"]
        DeviceID = request["DeviceId"]
        tag = request["tag"]
    ret = query_points(uuid, DeviceID, tag, vc)
    log.debug(r"response form virtualMachine_update: %s" % ret)
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
                    user.is_staff=True
                    user.save()
                   
                    return render_to_response('login.html')
                else:
                    error="Please input the same password"
            else:
                error="The username has existed,please change you username" 
        else:
            error="The email is invalid,please change your email"       
    return render_to_response('register.html',{'error':error})
@login_required(login_url='/accounts/login') 
def logout(request):
    return render_to_response('login.html')
@login_required(login_url='/accounts/login')       
def usersManager(request):
    return render_to_response('users.html',RequestContext(request))
@login_required(login_url='/accounts/login')    
def management(request):
    return render_to_response('Management.html',RequestContext(request))
    
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
    #jobs = CurrentModel.objects(name="job_result")
    jobs = queryCur.byName("job_result")
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
    #datasets = CurrentModel.objects(name="agent_plugin_list",uuid=id)
    datasets = queryCur.query(name="agent_plugin_list",uuid=id)
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
    log.debug("response form vmControl:%s" % perf)
    return HttpResponse(json.dumps(perf))
    
def fetch_perf(request):
    try:
        vm_name = request.GET.get("vmName")
        jid = request.GET.get("jid")
    except:
        vm_name = request["vmName"]
        jid = request["jid"]
    #objs = CurrentModel.objects(name="job_result",job_id=jid)
    objs = queryCur.query(name="job_result",job_id=jid)
    perf = dict()
    Status = dict(poweron="poweredOn", poweroff="poweredOff", suspend="suspended", reboot="poweredOn")
    if objs:
        for obj in objs:
            if obj.value["result"]:
                perf = dict(is_co=1, status=Status[obj.value["op"]])
    else:
         perf = dict(is_co=0, status="error")  
    log.debug("response form feth_perf:%s" % perf)
    return HttpResponse(json.dumps(perf))
    