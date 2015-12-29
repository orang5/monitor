# -*- coding: utf-8 -*-
import threading, time, commands, os
import Queue

import projectroot
import agent_utils
from agent_types import *
log = agent_utils.getLogger()

# baseclass for pooled worker thread
# extracted from commandbroker class.
class Worker(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.queue = q
        self.setDaemon(True)
        self.flag = False
        self.busy = False
        # self.retvar = 0

    def run(self):
        log.info("[pool] 新线程 %s" % self.name)
        while not self.flag:
            # will wait here for work
            m = self.queue.get()        # todo: if idle for N secs, finish self
            # set busy flag
            self.busy = True
            self.work(m)
            self.queue.task_done()
            self.busy = False
    
    # to be implemented in subclasses
    def work(self, met): pass

# encap of original pooling routine.
max_worker = 2
class ThreadPool(object):
    def __init__(self, cls):
        self.workers = []
        self.queue = Queue.Queue()
        self.worker_class = cls
        
    @property
    def nworker(self): return len(self.workers)
        
    def add_job(self, j):
        if True and self.nworker < max_worker:    # todo: if (all workers are busy)
            w = self.worker_class(self.queue)
            w.start()
            self.workers.append(w)
        self.queue.put(j)

class TestWorker(Worker):
    def work(self, m):
        m.last_value = m.value
        m.ts['execute'] = time.time()
        log.info("[%s] %s" % (self.name, m.cmdline()))
        m.value = os.popen(m.cmdline()).read().rstrip("\n\r")
        m.ts['latest'] = time.time()
        log.debug("[shell] %s" % m.message_json())

def _test():
    met1 = Metric("test.echo", "config", 30, r'echo %%var%%', "True")
    met1.args['var'] = 'USERNAME'
    met2 = Metric("test.echo", "config", 30, r'echo %%var%%', "True")
    met2.args['var'] = 'MONITOR_HOME'

    pool = ThreadPool(TestWorker)
    pool.add_job(met1)
    pool.add_job(met2)

    time.sleep(0.5)
    print met1
    print met2
    
if __name__ == "__main__" : _test()