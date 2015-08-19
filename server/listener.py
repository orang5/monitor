import sys
sys.path.append('..')

from transfer import create_engine,Queue,receive
from web.models import MoniterModel,DeviceModel
from datetime import datetime
import logging, json, threading

def callback(ch, method, properties, body):
    logging.info(" [x] %r:%r" % (method.routing_key, body,))
    message = json.loads(body)
    re_uuid = message['uuid']
    re_timestamp = message['time']
    infos = message['info']
    document = message['document']
    if document == 'MoniterModel':
        for info in infos:
            for key, value in info.iteritems():
                deviceID = key
                for k,v in value.iteritems():
                    model = MoniterModel(UUID = re_uuid, KEY = k, VALUE = json.dumps(v), TIME = datetime.strptime(re_timestamp,'%Y-%m-%d %H:%M:%S'), DEVICEID = deviceID)
                    model.save()
    if document == 'DeviceModel':
        query = DeviceModel.objects(UUID=re_uuid)
        if not query:
            model = DeviceModel(UUID=re_uuid, CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))
            model.save()
        else:
            DeviceModel.objects(UUID=re_uuid).update(CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))

    ch.basic_ack(delivery_tag = method.delivery_tag)

def listener():
    queue = Queue('test', 'test')
    receive(queue, callback)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_engine('172.16.174.5')
    listener()
    cleaner()
