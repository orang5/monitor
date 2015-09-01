# manages id and info of current host/agent instance
import uuid, socket, os

mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
iplist = socket.gethostbyname_ex(hostname)[2]
pid = os.getpid()

# use host_id as host identification
def host_id():
    return mac

def _test():
    print host_id(), hostname, ip, iplist
    
if __name__ == "__main__" : _test()