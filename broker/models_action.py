﻿# -*- coding: utf-8 -*-
from mongoengine import *
from datetime import datetime
import json, time, numbers
import projectroot
from common import agent_utils
from common.agent_types import *
from common.models import *

debug = False
timespan = 3600

agent_utils.profiler.add_counter("update")

# display_name: alias for metric.name
names = dict(
    dev_cpu="cpu", 
    dev_mem="mem",
    dev_disk="logical_disk",
    dev_nic="network",
    program_list="installed_programs"
)
names["host_info"] = "host_info"

# action methods
# get latest item for given model and metric entry
#@agent_utils.profiler.counter
def current_item(met, mdl):
    return mdl.__class__.objects(__raw__=met.tagdict())

#@agent_utils.profiler.counter
def item_exists(met, mdl):
    return current_item(met, mdl).count() > 0

@agent_utils.profiler.counter
def save(met, mdl):
    if debug: print "- in save"    
    try:
        mdl.save()
    except:
        print met.message_json()
        raise
    
@agent_utils.profiler.counter
def save_one(met, mdl):
    if not debug:
        item = current_item(met, mdl)
       # print met.tagdict(), item.count()
        if item and item.count()>0:
            item.update(value=met.value, timestamp=mdl.timestamp)
            agent_utils.profiler.inc_counter("update")
        else:
            save(met, mdl)
         #   time.sleep(1)
    else:
        print "- in save_one"
        save(met, mdl)
        item = current_item(met, mdl)
        print met, mdl, item, item.count()
        print met.tagdict(), CurrentModel.objects(name="test_username")


def packtag(x): return "a%d" % x

# note: if value is string then do not pack 
@agent_utils.profiler.counter
def save_packed(met, mdl):
    if not isinstance(met.value, numbers.Number):
        save(met, mdl)
    else:
        offset = met.timestamp % timespan
        time_min = datetime.fromtimestamp(met.timestamp - offset)
        
        # find correct entry and alter it.
        search_keys = met.tagdict()
        search_keys["timestamp"] = time_min
        items = mdl.__class__.objects(**search_keys)
        if items.count() == 0:
            # no such entry, create it
           # newlist = [""] * timespan
           # newlist[offset] = met.value
           
           # Jan 15: use sparse(dict) instead of array
           # use padding space when init
            newdict = dict(padding="a"*4000)
            newdict[packtag(offset)] = met.value
            mdl.packed = True
            mdl.value = newdict
            mdl.timestamp = time_min
            mdl.save()
            # remove padding
            it = mdl.__class__.objects(**search_keys)
            it.update(unset__value__padding=1)
        else:
            # magic
            items.update(**{"set__value__%s" % packtag(offset) : met.value})

# metric type routes: describes how to deal with certain metric type
# to which model this metric is saved
routes = dict(
    config = ["ConfigModel", "CurrentModel"],         # config 
    metric = ["MetricModel", "CurrentModel"],         # metric/perf
    inventory = ["InventoryInfoModel", "CurrentInfoModel"],   # inventory
    current = ["CurrentModel"],   # current/runtime only save in currentmodel
    runtime = ["CurrentModel"],
    # todo
    log = ["LogModel"],
    flow = ["FlowModel"]
)

# model settings. currently only [latest]
# describes how to save into this model
actions = dict(
    ConfigModel         = save,
    MetricModel         = save_packed,
    InventoryInfoModel  = save,
    CurrentModel        = save_one,
    CurrentInfoModel    = save_one
)

def undottify(s):
    return s.replace("_", "..").replace(".", "_")

# factory method
# get specific metric model object from Metric object
def from_metric(met):
    ret = []
    for mdl in routes[met.type]:
        obj = MetricModel()
        if globals().has_key(mdl):
            obj = globals()[mdl]()
            if met.type == "inventory":
                obj.host = met.tags["uuid"]
                obj.display_name = names.get(met.name, met.name.replace(".", "_"))
        else:
            log.warning("unknown metric: %s", met.message_json())
        obj.name = met.name.replace(".", "_")
        obj.timestamp = datetime.fromtimestamp(met.timestamp)
        obj.value = met.value
        obj.packed = False
        for k, v in met.tags.iteritems():
            setattr(obj, k, v)
        ret.append(obj)  
    # print ret      
    return ret
    
# uniform save method
# save metric to each model defined in model_actions.py
@agent_utils.profiler.counter
def save_metric(met):
    for mdl in from_metric(met):
        cls = mdl.__class__.__name__
        act = actions[cls]
       # print "%s %s -> %s" % (act.__name__, cls, met.name)
        act(met, mdl)

if __name__ == "__main__":
    debug = True
    
    mm = Metric("test_username", "metric", 30, r'echo %USERNAME%', True)
    mm.value = 1
    mm.tags = {"hostname" : "host1", "cluster" : "cl01"}
    
    print "Metric: %s" % mm.message_json()
    save_metric(mm)
    
    
    