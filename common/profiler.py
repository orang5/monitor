# -*- coding: utf-8 -*-
import cProfile, pstats, StringIO, time

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
    
def test():
    print "test"
    
if __name__ == "__main__":
    print profile(test, 100)