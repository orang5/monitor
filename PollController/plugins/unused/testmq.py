# -*- coding: utf-8 -*-
from monitor_plugin import *
plugin_info("testmq.json")

flag = True

def dowork(met):
    met.value = agent_utils.run_cmd(met.cmd)
    print met
    return met

while flag:
    update_metrics(worker=dowork, publish=False)
    time.sleep(1)