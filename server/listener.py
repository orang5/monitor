from transfer import create_engine,Queue,receive
from web.models import MoniterModel
import logging, json, threading

def callback(ch, method, properties, body):
    logging.info(" [x] %r:%r" % (method.routing_key, body,))
    message = json.loads(body)
    re_uuid = message['uuid']
    re_timestamp = message['time']
    infos = message['info']
    for info in infos:
        for key, value in info.iteritems():
            deviceID = key
            for k,v in value.iteritems():
                model = MoniterModel(UUID = re_uuid, KEY = k, VALUE = json.dumps(v), TIME = re_timestamp, DEVICEID = deviceID)
                model.save()
    print " [x] %r:%r" % (method.routing_key, body,)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    
def listener():
    queue = Queue('test', 'test')
    receive(queue, callback)
    
if __name__ == '__main__':
    create_engine()
    listener()
    cleaner()