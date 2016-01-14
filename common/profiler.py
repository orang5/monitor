# -*- coding: utf-8 -*-
import cProfile, pstats, StringIO, time
import threading

# ---------------------------
# profiler interface

p = None
def reset():
    global p
    p = cProfile.Profile()
reset()

def start(): p.enable()
    
def stop(): p.disable()

def result():
    s = StringIO.StringIO()
    ps = pstats.Stats(p, stream=s).sort_stats("cumulative")
    ps.print_stats()
    return s.getvalue()
    
def profile(func, ntime=1, *args):
    reset()
    start()
    for i in xrange(0, ntime):
        func(*args)
    stop()
    return result()
    
# -----------------------
# timer interface
    
timers = {}
init = False
callback = None
running = False
th = None

def update_timer():
    global running
    global timers
    running = True
    while running:
        time.sleep(1)
        for it in timers.values():
            it["sec"] = it["count"]
            it["count"] = 0
        if callback: callback()

# decorator
def counter(func):
    def counted_func(*args):
        if not timers.has_key(func.__name__):
            timers[func.__name__] = dict(count=0, sec=0, total=0)
        #t = time.clock()
        tm = timers[func.__name__]
        func(*args)
        tm["count"] = tm["count"] + 1
        tm["total"] = tm["total"] + 1
        #tm["execute"] = time.clock() - t
    counted_func.__name__ = func.__name__
    return counted_func

def init_timer():
    global init
    if init: th.stop()    
    timers.clear()
    th = threading.Thread(target=update_timer)
    th.setDaemon(True)
    th.start()
    init = True
    
def stop_timer(): running = False

def print_timer():
    for k in timers.keys():
        print k, timers[k]
    print "------------------------"

init_timer()

@counter    
def test():
    print "test"
    
if __name__ == "__main__":
    init_timer()
    print profile(test, 100)
    stop_timer()
    print timers