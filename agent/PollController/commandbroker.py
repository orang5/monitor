# -*- coding: utf-8 -*-
import threading, time, commands, os
import Queue

import projectroot
import common.agent_utils
from common.agent_types import *
log = common.agent_utils.getLogger()

workqueue = Queue.Queue()
metric_callback = None

class CommandWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = workqueue
        self.flag = False
        self.setDaemon(True)
        # self.retvar = 0

    def run(self):
        log.info("[shell] %s" % self.name)
        while not self.flag:
            m = self.q.get()
            m.ts['execute'] = time.time()
            log.info("[%s] %s" % (self.name, m.cmdline()))
            
            m.value = os.popen(m.cmdline()).read().rstrip("\n\r")
            
            # commands.getstatusoutput(m.cmdline())
            m.ts['latest'] = time.time()
            
            if metric_callback:
                metric_callback(m)
            else: log.debug("[shell] %s" % m.message_json())
            self.q.task_done()

cmds = []
nworker = 2
workers = [CommandWorker() for i in xrange(0, nworker)]
for w in workers:
    w.start()
    time.sleep(0.1)

def queue(metric):
    metric.ts['queue'] = time.time()
    metric.last_value = metric.value
    workqueue.put(metric)

def _test():
    met = Metric("test.echo", "config", 30, r'echo %%var%%')
    met.args['var'] = 'USERNAME'
    print met

    queue(met)
    time.sleep(0.1)

    print met
    print met.cmdline(), " -> ", met.value, " time: ", met.ts["latest"] - met.ts["execute"]

#    time.sleep(1)

#    print met
if __name__ == "__main__" : _test()