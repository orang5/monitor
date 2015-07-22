# -*- coding: utf-8 -*-
import threading
import pika
from agent_types import Metric

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
        print "exchange: ", kwargs["exchange"]

    def queue_declare(self, **kwargs):
    #    if not kwargs.has_key("queue"): kwargs["queue"] = "mq_auto_queue"
        kwargs["queue"] = kwargs.get("queue", "mq_auto_queue")
        kwargs["durable"] = kwargs.get("durable", False)

        self.channel.queue_declare(**kwargs)
        self.queues[kwargs["queue"]] = kwargs
        print "queue: ", kwargs["queue"]

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
        
localq = None
remoteq = None
local_callback = None
remote_callback = None
local_conf = dict(exchange="monitor.exc", queue="monitor.local", routing_key="local", durable=True)
remote_conf = dict(exchange="monitor.remote", queue="monitor.remote", routing_key="remote", durable=True)

def subdict(dict, keys):
    return {k:dict[k] for k in keys}
   
# default callback wrapper, currying default args
def queue_callback(func):
    def _cb(channel, method, p, body):
        func(Metric.from_message_json(body))
        channel.basic_ack(delivery_tag = method.delivery_tag)
    return _cb

# use this library routine to init local q for monitor project
def setup_local_queue(callback=None):
    global localq
    global local_callback
    q = MQ(r"amqp://monitor:root@localhost:5672/")
    localq = q
    if callback: local_callback = callback
    
    q.connect()
    print "wait for local MQWorker..."
    while not q.worker.ready: pass
    q.exchange_declare(**subdict(local_conf, ["exchange", "durable"]))
    q.queue_declare(**subdict(local_conf, ["queue", "durable"]))
    q.queue_bind(**subdict(local_conf, ["exchange", "queue", "routing_key"]))
    if local_callback: q.add_consumer(local_conf["queue"], queue_callback(local_callback))
    return q

# use this library routine to init remote q for monitor project
# rkey is host identification.
def setup_remote_queue(callback=None):
    global remoteq
    global remote_callback
    q = MQ(r"amqp://monitor:root@192.168.133.1:5672/")
    remoteq = q
    if callback: remote_callback = callback

    q.connect()
    print "wait for remote MQWorker..."
    while not q.worker.ready: pass
    q.exchange_declare(**subdict(remote_conf, ["exchange", "durable"]))
    q.queue_declare(**subdict(remote_conf, ["queue", "durable"]))
    q.queue_bind(**subdict(remote_conf, ["exchange", "queue", "routing_key"]))
    if remote_callback: q.add_consumer(remote_conf["queue"], queue_callback(remote_callback))
    return q
    
def local_publish(msg): localq.publish(local_conf["exchange"], local_conf["routing_key"], msg)
def remote_publish(msg): remoteq.publish(remote_conf["exchange"], remote_conf["routing_key"], msg)

def _callback(body):
    print "Receive: ", body

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
    setup_local_queue(_callback)
    
    local_publish("1111111111111")
    local_publish("222222222222222")
    local_publish("3333333")
    local_publish("444444444444444")

    localq.close()

if __name__ == "__main__" : _test()