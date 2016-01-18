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

def add_counter(name):
    if not timers.has_key(name): timers[name] = dict(count=0, sec=0, total=0)
    
def inc_counter(name):
    timers[name]["count"] = timers[name]["count"] + 1
    timers[name]["total"] = timers[name]["total"] + 1
    
def refresh_counter(name):
    timers[name]["sec"] = timers[name]["count"]
    timers[name]["count"] = 0
    
def update_timer():
    global running
    global timers
    running = True
    while running:
        time.sleep(1)
        for k in timers.keys(): refresh_counter(k)            
        if callback: callback()

# decorator
def counter(func):
    def counted_func(*args):
        add_counter(func.__name__)
        #t = time.clock()
        func(*args)
        inc_counter(func.__name__)
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