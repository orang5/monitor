# -*- coding: utf-8 -*-
import projectroot
from common import agent_types, mq, agent_utils
from common.models import *
import time, datetime

log = agent_utils.getLogger()

def callback(met):
    # print "<debug>", met.message_json()
    #if met.type == "MoniterModel": return
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
        current_item(cur.__class__, met).delete()
        cur.save()

queue = mq.setup_remote_queue(callback)
queue.worker.join()