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

def virtualMachine(request):
    vm_id  = 'a41f724e5fb8'
    query = DeviceModel.objects(UUID=vm_id)
    for q in query:
        device_dict = {'CPU':json.loads(q.CPU),'DISK':json.loads(q.DISK),'MEMORY':json.loads(q.MEMORY),'NETWORK':json.loads(q.Network_Adapter)}
    return render_to_response('VirtualMachine.html',{'deviece':device_dict})


def virtualMachine_update(request):
    #vm_id = request.GET.get('uuid')
    vm_id  = 'a41f724e5fb8'
    device_id = request.GET.get('DeviceId')
    
    device_type = request.GET.get('DeviceType')
    #t = datetime.strptime('2015-05-02 21:12:12', '%Y-%m-%d %H:%M:%S')

    date_obj = datetime.fromtimestamp(float(request.GET.get('Time',time.time())))
    datasets = MoniterModel.objects(UUID = vm_id,DEVICEID = device_id,TIME=date_obj)
    info = []
    if device_type == 'cpu':
        LoadPercentage = []
        CurrentClockSpeed = []
        for data in datasets:
            info_dict = json.loads(data.VALUE)
            if data.KEY == 'cpu_CurrentClockSpeed':
                CurrentClockSpeed.append(info_dict['volume'])
            if data.KEY == 'cpu_LoadPercentage':
                LoadPercentage.append(info_dict['volume'])
        if LoadPercentage:
            info = dict(LoadPercentage=LoadPercentage, CurrentClockSpeed=CurrentClockSpeed)
        
    if device_type == 'mem':
        #info = dict(Capacity=[random.randint(0,100)])
        Free = []
        for data in datasets:
            info_dict = json.loads(data.VALUE)
            if data.KEY == 'mem_Free':
                Free.append(info_dict['volume'])
        info = dict(Free=Free)     
          
    if device_type == 'net':
        UpLoad = []
        DownLoad = []
        for data in datasets:
            info_dict = json.loads(data.VALUE)
            if data.KEY == 'net_bytes_in':
                UpLoad.append(info_dict['volume'])
            if data.KEY == 'net_bytes_out':
                DownLoad.append(info_dict['volume'])
        if UpLoad:
            info = dict(UpLoad=UpLoad, DownLoad=DownLoad)
            
    if device_type == 'disk':
        #info = dict(Read=[random.randint(0,100)], Write=[random.randint(0,100)])
        Read = []
        Write = []
        for data in datasets:
            info_dict = json.loads(data.VALUE)
            if data.KEY == 'io_stat_read':
                Read.append(info_dict['volume'])
            if data.KEY == 'io_stat_write':
                Write.append(info_dict['volume'])
        if Read:
            info = dict(Read=Read, Write=Write)
        
    return HttpResponse(json.dumps(info))

if __name__ == '__main__':
    from models import Employee
    for e in Employee.objects.all():
        print e["id"], e["name"], e["age"]    