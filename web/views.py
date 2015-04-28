from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
import json,random


def index(request):
    return render_to_response('index2.html')

def index_update(request):
    
    d1 = [58, 28, 30, 69, 16, 37, 40]
    d2 = [28, 48, 40, 19, 86, 27, 90]
    data = dict(data1=d1, data2=d2)
    return HttpResponse(json.dumps(data))

def virtualMachine(request):
    return render_to_response('VirtualMachine.html')

def virtualMachine_update(request):
    type = request.GET.get('type')
    if type == 'cpu':
        data = dict(LoadPercentage=random.randint(0,100), CurrentClockSpeed=random.randint(0,100))
    if type == 'mem':
        data = dict(Capacity=random.randint(0,100))
    if type == 'net':
        data = dict(UpLoad=random.randint(0,100), DownLoad=random.randint(0,100))
    if type == 'disk':
        data = dict(Read=random.randint(0,100), Write=random.randint(0,100))        
        
    return HttpResponse(json.dumps(data))

if __name__ == '__main__':
    from models import Employee
    for e in Employee.objects.all():
        print e["id"], e["name"], e["age"]    