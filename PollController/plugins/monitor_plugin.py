# -*- coding: utf-8 -*-
# this is the common import file for all monitor plugins
import sys, os, inspect, subprocess, shlex
up_one_level = os.path.dirname(os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe()))))
sys.path.append(up_one_level)

import time, json
import mq, agent_types, agent_utils

# init local mq queue with PollController
mq.setup_local_queue()

info = None
metrics = {}
ts = {}

def plugin_info(filename):
    global info
    global metrics
    
    # read PluginDesc from json file
    f = file(filename)
    d = json.load(f)
    f.close()
    # add class info
    d["__class__"] = d.get("__class__", "PluginDesc")
    for m in d["metrics"]:
        m["__class__"] = m.get("__class__", "MetricDesc")
        m["cmd"] = m.get("cmd", "")
        m["interval"] = m.get("interval", 0)
    info = agent_types.Plugin._make(agent_utils.from_json(agent_utils.to_json(d)))
    
    # sort Metric
    for m in info.metrics:
        metrics[m.interval] = metrics.get(m.interval, [])
        ts[m.interval] = time.time() - m.interval-1
        metrics[m.interval].append(agent_types.Metric._make(m))
    
def plugin_info_tags():
    return dict(plugin=info.name, pid=os.getpid())
    
def publish(met, debug=False):
    met.ts["latest"] = time.time()
    met.update_tags(**plugin_info_tags())
    if not debug:
        mq.local_publish(met.message_json())
    else: print "[" + info.name +"] publish -> ", met.message_json() 
    
# round-robin routine helper
# worker: update value for given Metric object. 
#   def worker(metric): metric.value = new_value
# - worker must be blocking
def update_metrics(worker, **kwargs):
    kwargs["publish"] = kwargs.get("publish", True)
    kwargs["group"] = kwargs.get("group", False)
    t = time.time()
    for intv in metrics.keys():
        if intv>0 and t > ts[intv]+intv:
            ts[intv] = t
            for met in metrics[intv]:
                met.ts["execute"] = time.time()
                met.last_value = met.value
            
            if not kwargs["group"]:
                for met in metrics[intv]:
                    worker(met)
                    if kwargs["publish"]: publish(met)
            else:
                worker(metrics[intv])
                if kwargs["publish"]:
                    for met in metrics[intv]: publish(met)
            
    print "[" + info.name +"] update_metrics -> ", time.time() - t, "secs"