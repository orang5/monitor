# -*- coding: utf-8 -*-
import agent_types
import mq
import time, datetime
from models import *

def callback(met):
    # print "<debug>", met.message_json()
    if met.type == "MoniterModel": return
    
    if not met.tags.has_key("uuid"):
        print "****** %s ******" % met.timestamp, met
        print "------ %s ------" % met.timestamp, mq._body
        met.tags["uuid"] = "empty-uuid"    
    
    mdl = from_metric(met)
    if mdl:
        '''
        try:
          print "[ " + str(mdl.__class__).split(".")[-1].replace("'>", "") + " ] " + met.name + " value=" + str(met.value) + " " +  " ".join(["%s=%s" % (k, v) for k, v in met.tags.iteritems()])
       #    print met.message_json()
        except: pass
        '''
        if isinstance(mdl, list):
          #  print "****************** ", len(mdl)
          #  if len(mdl)>100: print met
            for m in mdl:
                print "save ->", m.__class__, met.name, met.timestamp
                m.save()
        else:
            print "save ->", mdl.__class__, met.name, met.timestamp
            mdl.save()    
    elif met.type != "DeviceModel":
        print "received_else: ", met.message_json()

queue = mq.setup_remote_queue(callback)
queue.worker.join()