# -*- coding: utf-8 -*-
import threading, time
import pika
from agent_types import Metric
import agent_info

# use SelectConnection to maintain loop & consumers
# it's all async (very nasty)
# all callback methods (on_connect, on_channel, etc) only work after ioloop is up
# however, ioloop will block current thread, so
# must set up all callbacks BEFORE ioloop.start()
# ioloop.start() also do the actual connection work.
class MQWorker(threading.Thread):
    def __init__(self, mq):
        threading.Thread.__init__(self)
        self.mq = mq
        self.conn = None
        self.ready = False
        self.channel = None
        self.consumers = {}
        self.setDaemon(True)

    def connect(self):
        print "MQWorker: open SelectConnection (data flow) -> ", self.mq.url
        self.conn = pika.SelectConnection(pika.URLParameters(self.mq.url), self._on_connect)

    def _on_connect(self, conn):
#        print "in _on_connect"
        self.conn #= conn
        self.create_channel()

    def create_channel(self):
        print "in create_channel"
        self.channel = self.conn.channel(self._on_channel)

    def _on_channel(self, chn):
#        print "in _on_channel"
        self.channel = chn
        self.ready = True
        print "MQWorker: connection is ready."

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.channel = None
            print "MQWorker: SelectConnection is closed."

    # recv = add consumer
    def add_consumer(self, qname, callback):
        self.consumers[qname] = self.consumers.get("qname", {})

        cid = self.channel.basic_consume(callback, qname)
        self.consumers[qname][cid] = dict(cid=cid, queue=qname, callback=callback)

    def run(self):
        print "start ioloop..."
        self.conn.ioloop.start()
        print self.name, " is exiting..."

# basic MQ object, use BlockingConnection to set attributes
# DO NOT set Exclusive flag for objects
# for they will be used in another connection (MQWorker).
class MQ(object):
    def __init__(self, urlparam):
        self.url = urlparam
        self.conn = None
        self._channel = None
        self.exchanges = {}
        self.queues = {}
        self.worker = None
        self.mainloop = None

    def connect(self):
        # self.exchanges.clear()
        # self.queues.clear()
        # self.consumers.clear()
        print "open BlockingConnection (control flow) -> ", self.url
        self.conn = pika.BlockingConnection(pika.URLParameters(self.url))
    #    print self.conn
        self.channel = self.conn.channel()
    #    print self.channel
        self.worker = MQWorker(self)
        self.worker.connect()
        self.worker.start()

        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.channel = None
            print "BlockingConnection is closed."
        if self.worker:
            self.worker.close()

    # use default channel to define exchange/queue
    def exchange_declare(self, **kwargs):
        kwargs["exchange"] = kwargs.get("exchange", "mq_auto_exc")
        self.channel.exchange_declare(**kwargs)
        self.exchanges[kwargs["exchange"]] = kwargs
#        print "exchange: ", kwargs["exchange"]

    def queue_declare(self, **kwargs):
    #    if not kwargs.has_key("queue"): kwargs["queue"] = "mq_auto_queue"
        kwargs["queue"] = kwargs.get("queue", "mq_auto_queue")
        kwargs["durable"] = kwargs.get("durable", False)

        self.channel.queue_declare(**kwargs)
        self.queues[kwargs["queue"]] = kwargs
#        print "queue: ", kwargs["queue"]

    # 将queue与exc绑定，和channel无关（channel不被绑定）
    def queue_bind(self, exchange, queue, routing_key):
        if not self.exchanges.has_key(exchange): self.exchange_declare(exchange=exchange)
        if not self.queues.has_key(queue): self.queue_declare(queue=queue)

        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)
        print "bind: (", exchange, ",", routing_key,  ") -> queue:", queue

    # send = publish
    def publish(self, exc, rkey, msg):
        if not self.exchanges.has_key(exc): self.exchange_declare(exchange=exc)

        self.channel.basic_publish(exchange=exc, routing_key=rkey, body=msg)

    # recv = add consumer
    def add_consumer(self, qname, callback):
        if not self.queues.has_key(qname): self.queue_declare(queue=qname)
        self.worker.add_consumer(qname, callback)
        print "start consuming from queue:", qname
        
# default callback wrapper, currying default args
def queue_callback(func, parse=True):
    parser = (lambda x: x)
    if parse: parser = Metric.from_message_json
    def _cb(channel, method, p, body):
        func(parser(body))
        channel.basic_ack(delivery_tag = method.delivery_tag)
    return _cb

# wrapper for wrapper methods
def _init_queue(q, dir = "local", type = "dat", key = "m", callback = None, parse = True, durable = True, prefix = "m"):
    ename = "%s.exc" % prefix
    qname = "%s.%s.%s" % (prefix, dir, type)
    
    print "[init_queue] exchange=%s queue=%s key=%s" % (ename, qname, key)
    
    q.exchange_declare(exchange=ename, durable=durable)
    q.queue_declare(queue=qname, durable=durable)
    q.queue_bind(ename, qname, key)
    if callback: q.add_consumer(qname, queue_callback(callback, parse))
    
def _publish(q, msg, dir = "local", type = "dat", key = "m", prefix = "m", dry=False):
    ename = "%s.exc" % prefix
    qname = "%s.%s.%s" % (prefix, dir, type)
    
    if not dry: q.publish(ename, key, msg)
    else: print "[publish] [%s] %s" % (qname, msg)
    
localq = None
remoteq = None

# use this library routine to init local q for monitor project
def setup_local_queue(data=None, control=None):
    global localq
    q = MQ(r"amqp://monitor:root@localhost:5672/")
    localq = q
    
    q.connect()
    print "wait for local MQWorker..."
    while not q.worker.ready: pass
    
    _init_queue(q, callback=data)
    _init_queue(q, type="con.%s" % agent_info.pid, key = str(agent_info.pid), callback=control, parse=False)
    return q

# use this library routine to init remote q for monitor project
# routing key is host identification.
def setup_remote_queue(data=None, control=None):
    global remoteq
    
    q = MQ(r"amqp://monitor:root@192.168.133.1:5672/")
    remoteq = q

    q.connect()
    print "wait for remote MQWorker..."
    while not q.worker.ready: pass
    
    _init_queue(q, dir="remote", callback=data)
    _init_queue(q, type="con.%s" % agent_info.host_id(), key=agent_info.host_id(), callback=control, parse=False)
    return q

# local plugin uses [local_publish] to send metrics to plugin_manager
def local_publish(msg): _publish(localq, msg)

# plugin_manager uses [remote_publish] to send metrics to transfer_broker (server)
def remote_publish(msg): _publish(remoteq, msg, dir="remote")

# plugin_manager uses [local_control] to send control to certain plugin (pid)
def local_control(msg, pid): _publish(localq, msg, type="con.%s" % pid, key=str(pid))

# server uses [remote_control] to send control to certain host (plugin_manager)
def remote_control(msg, host_id): _publish(remoteq, msg, type="con.%s" % host_id, key=str(host_id)) 

def _callback(body):
    print "Receive: ", body
    
def _con_callback(body):
    print "Receive control msg: ", body

def _test():
#    m = MQ(r'amqp://guest:guest@localhost:5672/')
#    m.connect()
#    m.queue_bind("myexc", "myqueue", "test")
#    m.add_consumer("myqueue", _callback)
#    m.publish("myexc", "test", "11111111111111")
#    m.publish("myexc", "test", "22222222222222")
#    m.publish("myexc", "test", "33333333333333")
#    m.publish("myexc", "test", "44444444444444")
#    m.close()
    setup_local_queue(_callback, _con_callback)
    
    local_publish("1111111111111")
    local_publish("222222222222222")
    local_publish("3333333")
    local_publish("444444444444444")
    
    local_control("1111111", agent_info.pid)
    local_control("22222222222", agent_info.pid)
    
    time.sleep(3)

    localq.close()

if __name__ == "__main__" : _test()