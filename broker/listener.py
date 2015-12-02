# -*- coding: utf-8 -*-
import time, datetime
import projectroot
from common import agent_types, mq, agent_utils, threadpool
import analyzer, models_action

log = agent_utils.getLogger()

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
def callback(met): pool.add_job(met)

queue = mq.setup_remote_queue(callback)
queue.worker.join()
