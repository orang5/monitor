# -*- coding: utf-8 -*-
import agent_types
import mq
import time, datetime
from models import *

def callback(met):
    mdl = from_metric(met)
    if mdl:
        print "[ " + str(mdl.__class__).split(".")[-1].replace("'>", "") + " ] " + met.name + " value=" + str(met.value) + " " +  " ".join(["%s=%s" % (k, v) for k, v in met.tags.iteritems()])
        if isinstance(mdl, list):
            for m in mdl: m.save()
        else:
            mdl.save()    
    else:
        print "received_else: ", met.message_json()

queue = mq.setup_remote_queue(callback)
queue.worker.join()