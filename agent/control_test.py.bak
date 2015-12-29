# -*- coding: utf-8 -*-
import commandbroker, projectroot
from common import agent_utils, agent_info, mq, config
from common.agent_types import *
import time

reply_flag = False
reply = None

def cb(msg):
    global reply_flag
    global reply
    d = agent_utils.from_json(msg)
    reply = d
    reply_flag = True
    
def blocked_request(*args):
    global reply_flag
    reply_flag = False
    mq.request(*args)
    while not reply_flag: time.sleep(0.1)
    return reply

id = config.vsphere_id
ip = config.vsphere_agent
q = mq.connect_control(id, "remote", ip, cb)

time.sleep(1)

# get plugin info
req = dict(op="plugin_info", uuid=id)
plugin_info = blocked_request(agent_utils.to_json(req), id)

for k in plugin_info.keys():
    if k == "monitor_vsphere": continue
    print "-------- %s --------" % k
    req = dict(op="test", uuid=id, pid=plugin_info[k]["pid"])
    perf = blocked_request(agent_utils.to_json(req), id)
    print perf
    
