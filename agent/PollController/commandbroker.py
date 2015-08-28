# -*- coding: utf-8 -*-
import time, commands, os
import projectroot
from common import agent_utils, threadpool
from common.agent_types import *
log = agent_utils.getLogger()

metric_callback = None

class CommandWorker(threadpool.Worker):
    def work(self, m):
        m.last_value = m.value
        m.ts['execute'] = time.time()
        log.info("[%s] %s" % (self.name, m.cmdline()))
        m.value = os.popen(m.cmdline()).read().rstrip("\n\r")
        m.ts['latest'] = time.time()
        if metric_callback:
            metric_callback(m)
        else: log.debug("[shell] %s" % m.message_json())

pool = threadpool.ThreadPool(CommandWorker)
def queue(metric): pool.add_job(metric)

def _test():
    met1 = Metric("test.echo", "config", 30, r'echo %%var%%', "True")
    met1.args['var'] = 'USERNAME'
    met2 = Metric("test.echo", "config", 30, r'echo %%var%%', "True")
    met2.args['var'] = 'MONITOR_HOME'
    
    queue(met1)
    queue(met2)
    time.sleep(0.5)

    print met1
    print met2

if __name__ == "__main__" : _test()