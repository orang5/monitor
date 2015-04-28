from WindowsWatcher import WinWatcher
from LinuxWatcher import LinuxWatcher
from transfer import create_engine, Queue, send
import platform, threading, time, win_watcher, json
import uuid

node = uuid.getnode()
machine_uuid = uuid.UUID(int = node).hex[-12:]

agent = None

if platform.system()=='Windows':
    agent = WinWatcher()
elif platform.system()=='Linux':
    agent = LinuxWatcher()
else:
    raise    
    
def cpu_use():
    return agent.cpu_use()

def mem_use():
    return agent.mem_use()

def get_fs_info():
    return agent.get_fs_info()

def network():
    return agent.network()    
    
class Sender(threading.Thread):
    def __init__(self,func, interval):     
        super(Sender, self).__init__()           
        self.interval = interval
        self.func = func
        #self.queue = Queue('test', 'test')
    
        
    def run(self):
        global machine_uuid
        queue_test = Queue('test', 'test')
        while True:
            timestamp = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            msg = dict(uuid=machine_uuid,info=self.func(),time = timestamp)
            #self.queue.send(json.dumps(msg))
            send(json.dumps(msg),queue_test)
            #print timestamp
            time.sleep(self.interval)
            
def start_all(funcs, intervals):
    for f,t in zip(funcs,intervals):
        t = Sender(f, t)
        t.start()
    


        
if __name__ == '__main__':
    create_engine()
    funcs = [cpu_use, mem_use,network,get_fs_info]
    intervals = [0,1,0,1]    
    start_all(funcs,intervals)