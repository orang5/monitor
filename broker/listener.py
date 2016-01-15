# -*- coding: utf-8 -*-
import time, datetime
import projectroot
from common import agent_types, mq, agent_utils, threadpool
import analyzer, models_action

log = agent_utils.getLogger()

def build_metric(name, v, t={}):
    met = agent_types.Metric(name, "metric", 30, "", True)
    met.tags = t
    met.value = v
    return met

def do_work(met):
    # in-line analyze routine, now too simple to become a method
    # def do_analyze(met):
    for a in analyzer.list:
        if a.check(met): a.action(met)
    # save
    models_action.save_metric(met)

def do_test(met):
    print met

class MetricWorker(threadpool.Worker):
    def work(self, met):
        do_work(met)
     #  do_test(met)


# simply add metric to thread pool
# so that original callback will return immediately
pool = threadpool.ThreadPool(MetricWorker)
def callback(met): 
    pool.add_job(met)
    # do_work(met)
    # do_test(met)

n=20
def profiler_callback():
    global n
    counter = agent_utils.profiler.timers["save"]
    n=n+1
    if n>20:
        n=0
        print "消息数量 当前\t总计"
        print "--------------------------"
    print "\t %d" % counter["sec"], "\t", counter["total"]

agent_utils.profiler.callback = profiler_callback
queue = mq.setup_remote_queue(callback)

while True:
    time.sleep(3)
    ts = agent_utils.profiler.timers
    for k in ts.keys():
        met_total = build_metric("broker_perf", ts[k]["total"], dict(func=k, stat="total"))
        met_sec   = build_metric("broker_perf", ts[k]["sec"], dict(func=k, stat="sec"))
        do_work(met_total)
        do_work(met_sec)
  #  for k in agent_utils.profiler.timers.keys():
  #      print k, agent_utils.profiler.timers[k]["sec"]
    