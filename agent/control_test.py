# -*- coding: utf-8 -*-
import commandbroker, projectroot
from common import agent_utils, agent_info, mq, config
from common.agent_types import *
import time

reply = None
jobs = {}

jid_impl = 0
def jid():
    global jid_impl
    jid_impl = jid_impl + 1
    return str(jid_impl)

def cb(msg):
    global jobs
    global reply
    d = agent_utils.from_json(msg)
    reply = d
    jobs[d["job_id"]] = True
    
def blocked_request(req):
    global jobs
    j = req["job_id"] = jid()
    uuid = req["uuid"]
    jobs[j] = False
    
    print "send >>> ", req
    mq.request(agent_utils.to_json(req), uuid)
    while not jobs[j]: time.sleep(0.1)
    return reply

id = config.vsphere_id
ip = config.vsphere_agent
q = mq.connect_control(id, "remote", ip, cb)

time.sleep(1)

print "---------- get plugin info ----------"
req = dict(op="plugin_info", uuid=id)
plugin_info = blocked_request(req)

print "---------- plugin reply test ----------"
for k in plugin_info.keys():
    if k == "job_id": continue
    print "-------- %s --------" % k
    req = dict(op="test", uuid=id, pid=plugin_info[k]["pid"])
    print "<<<", blocked_request(req)
    
print "----------- test open vm -----------"
#req = dict(op="poweron", uuid=id, pid=plugin_info["monitor_vsphere"]["pid"], name="win7")
#print "<<<", blocked_request(req)

#req = dict(op="reboot", uuid=id, pid=plugin_info["monitor_vsphere"]["pid"], name="master0.islab.org")
#print "<<<", blocked_request(req)

req = dict(op="reboot", uuid=id, pid=plugin_info["monitor_vsphere"]["pid"], name="master0.islab.org")
print "<<<", blocked_request(req)

q.close()
