from mongoengine import *
from datetime import datetime
import json, time

connect('MoniterDB')

class MoniterModel(Document):
    UUID = StringField(max_length=255, min_length=1)
    DEVICEID = StringField(max_length=255, min_length=1)
    KEY = StringField(max_length=255, min_length=1)
    VALUE = StringField(max_length=255, min_length=1)
    TIME = DateTimeField(default=datetime.now())

class DeviceModel(Document):
    UUID = StringField(max_length=255, min_length=1)
    CPU = StringField(max_length=255, min_length=1)
    MEMORY = StringField(max_length=255, min_length=1)
    Network_Adapter = StringField(max_length=255, min_length=1)
    DISK = StringField(max_length=255, min_length=1)

class platform(Document):
    VMLIST = StringField()


if __name__ == '__main__':
    #MoniterModel.objects.delete()
    #DeviceModel.objects.delete()
    #raise
    #datasets = MoniterModel.objects(UUID = 'a41f724e5fb8')
    #for e in datasets:
    #    print e.TIME, e.KEY, e.UUID, e.DEVICEID
    #vm_id  = 'a41f724e5fb8'
    #query = DeviceModel.objects(UUID=vm_id)
    #for q in query:
        #device_dict = {'CPU':q.CPU,'DISK':q.DISK,'MEMORY':q.MEMORY,'NETWORK':query[0].Network_Adapter}

    #for e in DeviceModel.objects().all():
        #print e.UUID, e.CPU, e.MEMORY, e.Network_Adapter, e.DISK

    vm_id = 'a41f724e5fb8'
    #device_type = 'mem'

    device_id = 'Physical Memory 0'
    ##sec = float(reqest.GET.get('Time',time.time()))
    t = datetime.strptime('2015-05-04 11:04:33', '%Y-%m-%d %H:%M:%S')
    t1 = t.timetuple()
    t2 = time.mktime(t1)
    t3 = datetime.fromtimestamp(t2)
    #print t2

    datasets = MoniterModel.objects(UUID = vm_id,DEVICEID = device_id,TIME=t3)
    info = {}
    for data in datasets:
        info_dict = json.loads(data.VALUE)
        if isinstance(info_dict, dict):
            info[data.KEY] = [info_dict['volume']]
        else:
            info[data.KEY] = data.VALUE

    print info
