# -*- coding: utf-8 -*-
import time, datetime
import projectroot
from common import agent_types, mq, agent_utils, threadpool
from common.models import *
import analyzer

log = agent_utils.getLogger()

def do_work(met):
    # print "<debug>", met.message_json()
    #if met.type == "MoniterModel": return
    
    # in-line analyze routine, now too simple to become a method
    # def do_analyze(met):
    for a in analyzer.list:
        if a.check(met): a.action(met)
    
    '''
    if not met.tags.has_key("uuid"):
        print "****** %s ******" % met.timestamp, met
        print "------ %s ------" % met.timestamp, mq._body
        met.tags["uuid"] = "empty-uuid"    
    '''
    mdl = from_metric(met)
    cur = current_metric(met)
    
    if mdl:
        if isinstance(mdl, list):
            '''
            if len(mdl)>100:
                log.warning(met)
                log.warning("list length: %d" % len(mdl))
            '''
            for m in mdl:
                # log.info(" ".join(("save ->", str(m.__class__), met.name, str(met.timestamp))))
                print " ".join(("save ->", m.__class__.__name__, met.name, str(met.timestamp)))
                m.save()
        else:
            # log.info(" ".join(("save ->", str(mdl.__class__), met.name, str(met.timestamp))))
            print " ".join(("save ->", mdl.__class__.__name__, met.name, str(met.timestamp)))
            mdl.save()
    elif met.type not in ["DeviceModel", "current"]:
        log.warning("received_else: %s" % met.message_json())
        
    if cur:
#        if met.name == "Vim25Api_EventEx":
#            print met.message_json()
#            print cur.__class__
        current_item(cur.__class__, met).delete()
        cur.save()

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