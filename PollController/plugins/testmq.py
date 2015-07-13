# -*- coding: utf-8 -*-
import sys, os, inspect, subprocess, shlex
up_one_level = os.path.dirname(os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe()))))
sys.path.append(up_one_level)

import time
import mq, agent_types, agent_utils

cmd = r"echo %USERNAME%"
interval = 30
flag = True

mq.setup_local_queue()

while flag:
    value = agent_utils.run_cmd(cmd)
    m = agent_types.Metric(name="test.username", value_type="config", interval=interval, cmd="")
    m.value = value
    mq.local_publish(m.message())
    time.sleep(interval)