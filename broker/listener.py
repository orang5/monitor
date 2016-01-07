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
    # pool.add_job(met)
    do_work(met)

queue = mq.setup_remote_queue(callback)

while True:
    time.sleep(1)
    m = build_metric("broker_perf", agent_utils.profiler.timers)
    pool.add_job(m)
  #  for k in agent_utils.profiler.timers.keys():
  #      print k, agent_utils.profiler.timers[k]["sec"]
    