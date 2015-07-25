# -*- coding: utf-8 -*-
import agent_types
import mq
import time, datetime
from models import *

def callback(met):
    # backport
    re_uuid = met.tags["uuid"]
    re_ts = met.timestamp
    infos = met.value
    print "received_all: ", met.message_json()
    if met.type == "MoniterModel":
        for info in infos:
            for key, value in info.iteritems():
                deviceID = key
                for k,v in value.iteritems():
                    model = MoniterModel(UUID = re_uuid, KEY = k, VALUE = json.dumps(v), TIME = datetime.fromtimestamp(re_ts), DEVICEID = deviceID)
                  #  print "save -> ", met
                    model.save()
    elif met.type == "DeviceModel":
        query = DeviceModel.objects(UUID=re_uuid)
        if not query:
            model = DeviceModel(UUID=re_uuid, CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))
          #  print "save -> ", met
            model.save()
        else:
            DeviceModel.objects(UUID=re_uuid).update(CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))

    else:
        print "received_else: ", met.message_json()

queue = mq.setup_remote_queue(callback)
queue.worker.join()