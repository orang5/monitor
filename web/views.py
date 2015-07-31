from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from datetime import datetime
from models import MoniterModel,DeviceModel
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

def virtualMachine_static(request):
    vm_id = request.GET.get('uuid')
    query = DeviceModel.objects(UUID=vm_id)
    for q in query:
        device_dict = {'CPU':json.loads(q.CPU),'DISK':json.loads(q.DISK),'MEMORY':json.loads(q.MEMORY),'NETWORK':json.loads(q.Network_Adapter)}    
    return render_to_response('VirtualMachine_static.html',{'deviece':device_dict})
    
def virtualMachine(request):
    vm_id = request.GET.get('uuid')
    query = DeviceModel.objects(UUID=vm_id)
    for q in query:
        device_dict = {'CPU':json.loads(q.CPU),'DISK':json.loads(q.DISK),'MEMORY':json.loads(q.MEMORY),'NETWORK':json.loads(q.Network_Adapter)}
    return render_to_response('VirtualMachine.html',{'deviece':device_dict})


def virtualMachine_update(request):
    vm_id = request.GET.get('uuid')
    device_id = request.GET.get('DeviceId')
    
    device_type = request.GET.get('DeviceType')
    #t = datetime.strptime('2015-05-04 11:04:35', '%Y-%m-%d %H:%M:%S')
    timestamp = request.GET.get('Time')
    date_obj = datetime.fromtimestamp(int(timestamp)/1000)
    datasets = MoniterModel.objects(UUID = vm_id,DEVICEID = device_id,TIME=date_obj)
    info = {}
    for data in datasets:
        #info_dict = json.loads(data.VALUE)
        #if isinstance(info_dict, dict):
            #info[data.KEY] = [info_dict['volume']]
        #else:
        info[data.KEY] = json.loads(data.VALUE)         
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