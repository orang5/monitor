# -*- coding: utf-8 -*-
from agent_types import *
import agent_utils, commandbroker, mq
import json, os, time, subprocess, shlex

plugins = []
metrics = {}
ts = {"init" : time.time()}
localq = None
remoteq = None

def load_plugin(fname):
    f = file(fname)
    d = json.load(f)
    f.close()
    # add class info
    d["__class__"] = d.get("__class__", "PluginDesc")
    for m in d["metrics"]:
        m["__class__"] = m.get("__class__", "MetricDesc")
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

def _test_callback(a, b, c, body):
    print "recv ", body

def init_queue():
    localq = mq.setup_local_queue(_test_callback)
    remoteq = mq.setup_remote_queue("test")

def start():
    while True:
        update()
        time.sleep(0.5)

def _test():
    init_queue()
    load_all("plugins")
    start()