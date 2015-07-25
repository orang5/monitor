# -*- coding: utf-8 -*-
from agent_types import *
import agent_utils, agent_info, commandbroker, mq
import json, os, time, subprocess, shlex

plugins = []
metrics = {}
ts = {"init" : time.time()}

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
    print "load_plugin ", p.name

    if p.type == "shell":
        for m in p.metrics:
            if not metrics.has_key(m.interval):
                metrics[m.interval] = []
                ts[m.interval] = time.time() - m.interval
            metrics[m.interval].append(Metric._make(m))
            print ">", m.name
    elif p.type == "platform":
        print "start platform plugin: ", p.cmd_list["start"]
        os.chdir("plugins") # hard coded here
        p.handle = subprocess.Popen(shlex.split(p.cmd_list["start"]))
        print "> pid =", p.pid
        os.chdir("..")
    return p

def load_all(path):
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            load_plugin("%s/%s" % (path,fname))

def send_metrics(met):
    # add tags
    met.update_tags(uuid=agent_info.host_id(), host=agent_info.hostname)
    if met.tags.has_key("plugin"):
        print "send_metrics: (", met.tags["plugin"], "):", met.message_json()
    else: print "send_metrics:", met.message_json()
    # send
    mq.remote_publish(met.message_json())
    print met.message_json()

def init_queue():
    mq.setup_remote_queue()
    mq.setup_local_queue(send_metrics)
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
    load_all("plugins")
    start()

if __name__ == "__main__" : _test()