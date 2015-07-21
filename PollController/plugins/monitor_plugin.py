# -*- coding: utf-8 -*-
# this is the common import file for all monitor plugins
import sys, os, inspect, subprocess, shlex
up_one_level = os.path.dirname(os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe()))))
sys.path.append(up_one_level)

import time, json
import mq, agent_types, agent_utils

info = None

def plugin_info(filename):
    global info
    f = file(filename)
    d = json.load(f)
    f.close()
    # add class info
    d["__class__"] = d.get("__class__", "PluginDesc")
    for m in d["metrics"]:
        m["__class__"] = m.get("__class__", "MetricDesc")
    info = agent_types.Plugin._make(agent_utils.from_json(agent_utils.to_json(d)))
    
def plugin_info_tags():
    return dict(plugin=info.name, pid=os.getpid())
    
def publish(met):
    met.ts["latest"] = time.time()
    met.update_tags(**plugin_info_tags())
    mq.local_publish(met.message_json())
    
mq.setup_local_queue()