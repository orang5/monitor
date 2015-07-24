# -*- coding: utf-8 -*-
from agent_types import *
import agent_utils, commandbroker
import json, os, time

plugins = []
metrics = {}
ts = {"init" : time.time()}

def load_plugin(fname):
    f = file(fname)
    d = json.load(f)
    f.close()
    # add class info
    if not d.has_key("__class__"): d["__class__"] = "PluginDesc"
    for m in d["metrics"]:
<<<<<<< HEAD
        if not m.has_key("__class__"): m["__class__"] = "MetricDesc"
    # print d
=======
        m["__class__"] = m.get("__class__", "MetricDesc")
        m["cmd"] = m.get("cmd", "")
        m["interval"] = m.get("interval", 0)
#    print d
>>>>>>> de176b8af2f6ab143bf201275dbe32b513e12f15
    # ugly......
    p = agent_utils.from_json(agent_utils.to_json(d))
    # append plugin and metrics to list
    plugins.append(p)
    for m in p.metrics:
        if not metrics.has_key(m.interval):
            metrics[m.interval] = []
            ts[m.interval] = time.time() - m.interval
        metrics[m.interval].append(Metric._make(m))

    return p

def load_all(path):
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            load_plugin("%s/%s" % (path,fname))

def update():
    now = time.time()
    for interval in metrics.keys():
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
