from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from datetime import datetime
from models import *
import json,random,time



def index(request):
    return render_to_response('index2.html')

def index_update(request):
    
    d1 = [58, 28, 30, 69, 16, 37, 40]
    d2 = [28, 48, 40, 19, 86, 27, 90]
    data = dict(data1=d1, data2=d2)
    return HttpResponse(json.dumps(data))

def vplatform(request):
    return render_to_response('Vplatform.html')

def network(request):
    return render_to_response('Network.html')

def virtualMachine_static1(request):
    vm_id = request.GET.get('uuid')
    query = InventoryInfoModel.objects(UUID=vm_id)
    for q in query:
        device_dict = {'CPU':json.loads(q.CPU),'DISK':json.loads(q.DISK),'MEMORY':json.loads(q.MEMORY),'NETWORK':json.loads(q.Network_Adapter)}
    return render_to_response('VirtualMachine_static.html', {'deviece':device_dict})

def virtualMachine_static(request):
    vm_id = request.GET.get('uuid')
    query = InventoryInfoModel.objects(uuid=vm_id)
    
    tmp = {}
    device_dict = {}
    
    for q in query:
        key = ''
        try:
            key = q.DeviceID
        except:pass
        tmp[key] = tmp.get(key, [])
        tmp[key].append(q);
    

    keys = tmp.keys(); keys.sort()
    for k in keys:
        current = max(tmp[k], key=lambda x: x.timestamp)
        key = current.display_name
        device_dict[key] = device_dict.get(key, [])
        device_dict[key].append(current);
        
    return render_to_response('VirtualMachine_static.html', {'deviece':device_dict})
    
def virtualMachine(request):
    pass    

def virtualMachine_update(request):
    vm_id = request.GET.get('uuid')
    DeviceId = request.GET.get('DeviceId') 
    
    timestamp = request.GET.get('Time')
    date_obj = datetime.utcfromtimestamp(int(timestamp)/1000)
    datasets = MetricModel.objects(uuid = vm_id,DeviceID = DeviceId,timestamp__gte=date_obj)
    info = {}
    for data in datasets:
        info[data.name] = data.value
    
    return HttpResponse(json.dumps(info))

def login(request):
    if request.method == 'POST':
        username = str(request.POST.get('username'))
        password = str(request.POST.get('password'))
        if (username.strip() == "islab@whu.edu") & (password.strip() == "whu"):
            return HttpResponseRedirect('index')
        else:
            return render_to_response('login.html',{'ushow':request.GET.get('username')})
            #return render_to_response('login.html')
    return render_to_response('login.html',{'ushow':'username'})

def usersManager(request):
    return render_to_response('users.html')
    
def management(request):
    return render_to_response('Management.html')
    
if __name__ == '__main__':
    from models import Employee
    for e in Employee.objects.all():
        print e["id"], e["name"], e["age"]