# -*- coding: utf-8 -*-
import commandbroker, projectroot
from common import agent_utils, agent_info, mq
from common.agent_types import *
import json, os, time, subprocess, shlex, threading

log = agent_utils.getLogger()
plugins = []
metrics = {}
ts = {"init" : time.time(), "heartbeat" : 0, "perf" : 0}
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
    log.info(u"监控插件: [%s] %s" % (p.type, p.name))

    if p.type == "shell":
        for m in p.metrics:
            if not metrics.has_key(m.interval):
                metrics[m.interval] = []
                ts[m.interval] = time.time() - m.interval
            metrics[m.interval].append(Metric._make(m))
            log.info(u"数据点 %s" % m.name)
    elif p.type == "platform":
        p.handle = subprocess.Popen(shlex.split(p.cmd_list["start"]))
        log.info(u"加载平台插件 %s, pid = %d" % (p.cmd_list["start"], p.pid))
        mq.connect_control(p.pid)
        # debug
        # mq.local_request(agent_utils.to_json(dict(op="open", vm="66ccff66ccff", host="a9b8c7d6e5f4")), p.pid)
    return p

def load_all(path):
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            load_plugin("%s/%s" % (path,fname))

# warning: synchronized
@agent_utils.profiler.counter
def send_metrics(met):
    global sending
    global ntime
    # log.debug("%s %s len=%d time=%d", met.name, str(met.tags), len(met.message_json()), met.timestamp)
    # log.debug("%s" % met.name)
        
    # add tags
    met.update_tags(uuid=agent_info.host_id(), host=agent_info.hostname)
    
    # send (with lock)
    if sending.acquire():
        mq.remote_publish(met.message_json())
        sending.release()

def control_callback(msg):
    print u"*** 插件返回结果:", msg
    mq.remote_reply(msg)
    d = agent_utils.from_json(msg)
    send_metrics(build_metric("job_result", d, dict(job_id=d["job_id"]), "metric"))

def control_callback_remote(msg):
    d = agent_utils.from_json(msg)
    jid = d["job_id"]
    print u"*** 服务端控制请求:", d
    # simple processing
    if d["op"] == "plugin_info":
        ret = get_plugin_info()
        ret["job_id"] = jid
        control_callback(agent_utils.to_json(ret))
    else:
        # directly send to plugin
        mq.local_request(msg, d["pid"])

def init_queue():
    mq.setup_remote_queue()
    mq.setup_local_queue(send_metrics)
    mq.setup_local_control(request=None, reply=control_callback)    
    try:
        mq.setup_remote_control(request=control_callback_remote)
        print u"服务端控制已启用."
    except:
        print u"服务端控制未启用."
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
    # update agent info
    if now-ts["heartbeat"] > heartbeat_interval:
        send_heartbeat_metrics()
        ts["heartbeat"] = now
    # update self-perf
    if now-ts["perf"] > 1:
        ts["perf"] = now
        #print agent_utils.profiler.timers
        met = build_metric("agent_perf", agent_utils.profiler.timers, type="metric")
        send_metrics(met)
                    
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
    ret = {}
    for p in plugins:
        if p.type == "platform":
            ret[p.name] = p.describe()
    return ret
   
def get_metric_info():
    mets = {}
    for group in metrics.values():
        for m in group:
            d = Metric.describe(m)
            d.update(
                value = m.value,
                tags = m.tags,
                timestamp = m.timestamp,
                ts = m.ts
            )
            mets[m.name] = d
    return mets

def build_metric(name, v, t={}, type="runtime"):
    met = Metric(name, type, 30, "", True)
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
