# -*- coding: utf-8 -*-
import commandbroker, projectroot
from common import agent_utils, agent_info, mq
from common.agent_types import *
import json, os, time, subprocess, shlex, threading

log = agent_utils.getLogger()
plugins = []
metrics = {}
ts = {"init" : time.time()}
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
    return p

def load_all(path):
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            load_plugin("%s/%s" % (path,fname))

# warning: synchronized
def send_metrics(met):
    global sending

    # add tags
    met.update_tags(uuid=agent_info.host_id(), host=agent_info.hostname)
    if met.tags.has_key("plugin"):
        log.debug(" ".join(("[", met.tags["plugin"], "]: [%d]" % met.timestamp, met.name, str(met.tags))))
    else:
        log.debug(" ".join(("[%d]" % met.timestamp, met.name, str(met.tags), str(len(met.message_json())) )) )

    # send (with lock)
    if sending.acquire():
        mq.remote_publish(met.message_json())
        sending.release()

def control_callback(msg):
    print "receive control:", msg

def init_queue():
    mq.setup_remote_queue()
    mq.setup_local_queue(send_metrics, control_callback)
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
                    
def start():
    while True:
        update()
        time.sleep(0.5)

def _test_callback(body):
    print "recv ", body

def _test():
    init_queue()
    os.chdir("plugins") # hard coded here
    load_all(".")    
    start()

if __name__ == "__main__" : _test()
