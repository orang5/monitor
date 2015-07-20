# -*- coding: utf-8 -*-
from monitor_plugin import *
plugin_info("testmq.json")

cmd = r"echo %USERNAME%"
interval = 30
flag = True

while flag:
    value = agent_utils.run_cmd(cmd)
    m = agent_types.Metric(name="test.username", type="config", interval=interval, cmd=cmd)
    m.value = value
    m.update_tags(**plugin_info_tags())
    publish(m)
    time.sleep(interval)