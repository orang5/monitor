# -*- coding: utf-8 -*-
import threading, time
import pika, traceback
from agent_types import Metric
import agent_info, agent_utils, config

log = agent_utils.getLogger()

# Sept 23: add watchdog for MQWorker
class MQWatchdog(threading.Thread):
    def __init__(self, mq):
        threading.Thread.__init__(self)
        self.mq = mq
        self.interval = 5
        self.flag = True
        
    def run(self):
        log.info("MQWatchdog: started for %s" % self.mq.url)
        while self.flag:
            time.sleep(self.interval)
            if self.mq.worker.recover_flag:
                log.warning("MQWatchdog: worker not running, recover...")
                self.mq.recover_worker()
                break
        log.info("MQWatchdog: exit.")

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
        self.recover_flag = False

    def connect(self):
        log.info("MQWorker: SelectConnection (data thread) -> %s" % self.mq.url)
        self.conn = pika.SelectConnection(pika.URLParameters(self.mq.url), self._on_connect)

    def _on_connect(self, conn):
        self.conn #= conn
        self.create_channel()

    def create_channel(self):
        self.channel = self.conn.channel(self._on_channel)

    def _on_channel(self, chn):
#        print "in _on_channel"
        self.channel = chn
        self.ready = True
        log.info("MQWorker: connection thread ready.")

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                log.info("MQWorker: SelectConnection closed.")
            except:
                log.warning("*** MQWorker: close failed. ***")
                traceback.print_exc()
            self.conn = None
            self.channel = None
            
    # recv = add consumer
    def add_consumer(self, qname, callback):
        self.consumers[qname] = self.consumers.get("qname", {})
        cid = self.channel.basic_consume(callback, qname)
        log.info("MQWorker: queue %s callback %s cid=%s" % (qname, callback.__name__, cid))
        self.consumers[qname][cid] = dict(cid=cid, queue=qname, callback=callback)

    def run(self):
        log.info("MQWorker: start ioloop...")
        try:
            self.conn.ioloop.start()
        except:
            traceback.print_exc()
            self.recover_flag = True
        log.info("MQWorker: %s is exiting..." % self.name)

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
        self.watch = None
        self.mainloop = None

    def connect(self):
        # self.exchanges.clear()
        # self.queues.clear()
        # self.consumers.clear()
        log.info("MQ: BlockingConnection (control flow) -> %s", self.url)
        self.conn = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.conn.channel()
        return self.conn
        
    def connect_worker(self):
        self.worker = MQWorker(self)
        self.worker.connect()
        self.worker.start()
        log.info("MQ: wait for local MQWorker...")
        while not self.worker.ready: pass
        self.watch = MQWatchdog(self)
        self.watch.start()
        
    def close(self):
        try:
            if self.conn:
                self.conn.close()
                log.info("MQ: BlockingConnection closed.")
        except:
            log.warning("MQ: *** cannot close self.conn, Exception: ***")
            traceback.print_exc()
        self.conn = None
        self.channel = None
        if self.watch:
            self.watch.flag = False
    
    # Sept 23: when crashed, we must recover
    def recover(self):
        log.warning("MQ: *** recover from crash ***")
        self.close()
        log.warning("MQ: *** reconnect ***")
        self.connect()
        log.warning("MQ: *** re-register exchange/queues ***")
        for v in self.exchanges.values():
            self.exchange_declare(**v)
        for v in self.queues.values():
            self.queue_declare(**v)
            if v.has_key("bind"):
                self.queue_bind(v["bind"]["exchange"], v["bind"]["queue"], v["bind"]["routing_key"])
        log.warning("MQ: *** recover complete. ***")
        
    def recover_worker(self):
        if not self.worker.recover_flag: return
        self.worker.recover_flag = False
        log.warning("MQWorker: *** recover from crash ***")
        self.worker.close()
        t = self.worker.consumers
        log.warning("MQWorker: *** reconnect ***")
        self.connect_worker()
        while not self.worker.ready: pass
        log.warning("MQ: *** re-register callbacks ***")
        for v in t.values():
            for value in v.values():
                self.worker.add_consumer(value["queue"], value["callback"])     
        log.warning("MQ: *** recover complete. ***")
        
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
        kwargs["auto_delete"] = kwargs.get("auto_delete", False)

        self.channel.queue_declare(**kwargs)
        self.queues[kwargs["queue"]] = kwargs
#        print "queue: ", kwargs["queue"]

    # 将queue与exc绑定，和channel无关（channel不被绑定）
    def queue_bind(self, exchange, queue, routing_key):
        if not self.exchanges.has_key(exchange): self.exchange_declare(exchange=exchange)
        if not self.queues.has_key(queue): self.queue_declare(queue=queue)

        self.channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)
        # Sept 23 add: save bind info for recover
        self.queues[queue]["bind"] = {"exchange" : exchange, "queue" : queue, "routing_key" : routing_key}
        
        log.info("".join(("MQ: bind: (", exchange, ",", routing_key,  ") -> queue:", queue)))

    # send = publish
    def publish(self, exc, rkey, msg):
        if not self.exchanges.has_key(exc): self.exchange_declare(exchange=exc)
        # retry until success
        while True:
            try:
                self.channel.basic_publish(exchange=exc, routing_key=rkey, body=msg)
                break
            except:
                log.warning("*** MQ: error in MQ.publish ***")
                traceback.print_exc()
                log.warning("*** MQ: start recover ***")
                self.recover()
                log.warning("*** MQ: retry publish... ***")

    # recv = add consumer
    def add_consumer(self, qname, callback):
        if not self.queues.has_key(qname): self.queue_declare(queue=qname)
        self.worker.add_consumer(qname, callback)
        log.info("MQ: consuming from queue - %s", qname)
        
# default callback wrapper, currying default args
def queue_callback(func, parse=True):
    parser = (lambda x: x)
    if parse: parser = Metric.from_message_json
    def _cb(channel, method, p, body):
        func(parser(body))
        channel.basic_ack(delivery_tag = method.delivery_tag)
    return _cb

# wrapper for wrapper methods
def _init_queue(q, dir = "local", type = "dat", key = "m", callback = None, parse = True, durable = True, prefix = "m", auto_delete = False):
    ename = "%s.exc" % prefix
    qname = "%s.%s.%s" % (prefix, dir, type)
    log.debug("exchange=%s queue=%s key=%s" % (ename, qname, key))
    
    q.exchange_declare(exchange=ename, durable=True)
    q.queue_declare(queue=qname, durable=durable, auto_delete=auto_delete)
    q.queue_bind(ename, qname, key)
    if callback: q.add_consumer(qname, queue_callback(callback, parse))
    
def _publish(q, msg, dir = "local", type = "dat", key = "m", prefix = "m", dry=False):
    ename = "%s.exc" % prefix
    qname = "%s.%s.%s" % (prefix, dir, type)
    
    if not dry: q.publish(ename, key, msg)
    else: log.debug("[%s] %s" % (qname, msg))
    
localq = None
remoteq = None
remotecon = None

# use this library routine to init local (agent<-plugin) DATA queue for monitor project
def setup_local_queue(data=None, parse=True):
    global localq
    q = MQ("amqp://monitor:root@localhost:5672/%%2f")
    localq = q    
    q.connect()
    q.connect_worker()    
    # data (plugin->agent). queue: m.local.dat routing_key: ld
    _init_queue(q, callback=handler, key="ld", parse=parse)    
    return q
    
# use this library routine to init remote (agent->broker) DATA queue for monitor project
def setup_remote_queue(data=None):
    global remoteq
    q = MQ("amqp://monitor:root@%s/%%2f" % config.mq_broker)
    remoteq = q
    q.connect()
    q.connect_worker()    
    # data (plugin->broker). queue: m.remote.dat routing_key: rd
    _init_queue(q, dir="remote", callback=data, key="rd")
    return q
    
# init local (agent<->plugin) control queues.
def setup_local_control(request=None, reply=None)
    if request:
        # request (agent->plugin) queue: m.local.[pid] routing_key: [pid]
        _init_queue(localq, type=str(agent_info.pid), key=str(agent_info.pid), callback=request, parse=False, durable=False, auto_delete=True)
    # reply (plugin->agent) queue: m.local.reply routing_key: lr
    _init_queue(localq, type="reply", key="lr", callback=reply, parse=False, durable=False, auto_delete=True)

def setup_remote_control(request=None, reply=None)
    if request:
        # request (server->agent) queue: m.remote.[hostid] routing_key: [hostid]
        _init_queue(remoteq, type=str(agent_info.pid), key=str(agent_info.pid), callback=request, parse=False, durable=False, auto_delete=True)
    # reply (agent->server) queue: m.remote.reply routing_key: rr
    _init_queue(remoteq, type="reply", key="rr", callback=reply, parse=False, durable=False, auto_delete=True)
    
#--------------------------
#           data
# plugin ---------> agent
#--------------------------
def local_publish(msg): _publish(localq, msg, key="ld")

#--------------------------
#          request
# agent ------------> plugin
#            pid
#--------------------------
def local_request(msg, pid): _publish(localq, msg, type=str(pid), key=str(pid))

#--------------------------
#           reply
# plugin ----------> agent
#--------------------------
def local_reply(msg): _publish(localq, msg, type="reply", key="lr")

#--------------------------
#          data
# agent ---------> broker
#--------------------------
def remote_publish(msg): _publish(remoteq, msg, dir="remote", key="rd")

#--------------------------
#           request
# server ------------> agent
#           host_id
#--------------------------
def remote_request(msg, host_id): _publish(remoteq, msg, dir="remote", type=str(host_id), key=str(host_id)) 

#--------------------------
#           reply
# plugin ----------> agent
#--------------------------
def remote_reply(msg): _publish(remoteq, msg, dir="remote", type="reply", key="rr")

g = False
def _callback(body):
    global g
    print "Receive: ", body
    if not g and body == "3333333":
        g = True
        raise
    
def _con_callback(body):
    print "Receive control msg: ", body

def _test():
    pass

if __name__ == "__main__" : _test()