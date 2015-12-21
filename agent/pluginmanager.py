# -*- coding: utf-8 -*-
import commandbroker, projectroot
from common import agent_utils, agent_info, mq
from common.agent_types import *
import json, os, time, subprocess, shlex, threading

log = agent_utils.getLogger()
plugins = []
metrics = {}
ts = {"init" : time.time(), "heartbeat" : time.time()}
heartbeat_interval = 30

sending = threading.Lock()

def load_plugin(fname):
    f = file(fname)
    d = json.load(f)
    f.close()
    # add class info
    d["__class__"] = d.get("__class__", "PluginDesc")
    for m in d["metrics"]:
        m["__class__"] = m.get("__class__", "MetricDesc")
        m["cmd"] = m.get("cmd", "")
        m["interval"] = m.get("interval", 0)
#    print d
    # ugly......
#    p = agent_utils.from_json(agent_utils.to_json(d))
#    print p
    p = Plugin._make(agent_utils.from_json(agent_utils.to_json(d)))
    # append plugin and metrics to list
    plugins.append(p)
    log.info(p.name)

    if p.type == "shell":
        for m in p.metrics:
            if not metrics.has_key(m.interval):
                metrics[m.interval] = []
                ts[m.interval] = time.time() - m.interval
            metrics[m.interval].append(Metric._make(m))
            log.info("[metric] %s" % m.name)
    elif p.type == "platform":
        log.info("start platform plugin -> %s" % p.cmd_list["start"])
        p.handle = subprocess.Popen(shlex.split(p.cmd_list["start"]))
        log.info("pid = %d" % p.pid)
        # debug
        mq.local_request('{"op" : "open", "vm" : "003ccf332154", "host" : "1a3c57092177"}', p.pid)
    return p

def load_all(path):
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            load_plugin("%s/%s" % (path,fname))

# warning: synchronized
def send_metrics(met):
    global sending
    log.debug("%s %s len=%d time=%d", met.name, str(met.tags), len(met.message_json()), met.timestamp)
        
    # add tags
    met.update_tags(uuid=agent_info.host_id(), host=agent_info.hostname)
    
    # send (with lock)
    if sending.acquire():
        mq.remote_publish(met.message_json())
        sending.release()

def control_callback(msg):
    print "receive from plugin:", msg

def control_callback_remote(msg):
    print "receive from server:", msg

def init_queue():
    mq.setup_remote_queue()
    mq.setup_local_queue(send_metrics)
    mq.setup_local_control(request=None, reply=control_callback)    
    try:
    #    mq.setup_remote_control_queue(control_callback_remote)
    except:
        print "** note: remote control disabled."
    commandbroker.metric_callback = send_metrics
   
def update():
    now = time.time()
    for interval in metrics.keys():
        if interval>0:
            if now-ts[interval] > interval:
                ts[interval] += interval
                # todo: change in queue strategy
                # current: queue all
                for m in metrics[interval]:
                    commandbroker.queue(m)
    # update heartbeat
    if now-ts["heartbeat"] > heartbeat_interval:
        send_heartbeat_metrics()
                    
def start():
    while True:
        update()
        time.sleep(0.5)
        
# Dec 1: add self monitor functions
#　retrieve agent information, and save into a dict
def get_agent_info():
    return dict(
        uuid = agent_info.host_id(),
        hostname = agent_info.hostname,
        ip = agent_info.ip, 
        pid = agent_info.pid,
        uptime = time.time() - ts["init"]
    )

def get_plugin_info():
    return [p.describe() for p in plugins if p.type == "platform"]
   
def get_metric_info():
    mets = []
    for group in metrics.values():
        for m in group:
            d = Metric.describe(m)
            d.update(
                value = m.value,
                tags = m.tags,
                timestamp = m.timestamp,
                ts = m.ts
            )
            mets.append(d)
    return mets

def build_metric(name, v, t={}):
    met = Metric(name, "runtime", 30, "", True)
    met.tags = t
    met.value = v
    return met
    
def send_heartbeat_metrics():
    send_metrics(build_metric("agent_info", get_agent_info()))
    send_metrics(build_metric("agent_plugin_list", get_plugin_info()))
    send_metrics(build_metric("agent_metric_list", get_metric_info()))

def _test_callback(body):
    print "recv ", body

def _test():
    init_queue()
    os.chdir("plugins") # hard coded here
    load_all(".")
    start()

if __name__ == "__main__" : _test()
