import logging, threading, functools

class _Engine(object):
    def __init__(self,connect):
        self.connect = connect
        
    def connect(self):
        return self.connect
    
engine = None
channel_test = None

def create_engine(host='localhost',port=5672,**kw):
    import pika
    global engine
    if engine is not None:
        raise DBError('Engine is already initialized.')
    params = dict(host=host,port=port)
    default = dict(virtual_host = None, credentials=None, channel_max=None, 
                   frame_max=None,heartbeat_interval=None,ssl_options=None,
                   connection_attempts=None,retry_delay=None,socket_timeout=None, 
                   locale=None,backpressure_detection=None)
    for k,v in default.iteritems():
        params[k] = kw.pop(k,v)
        
    params.update(**kw)
    try:
        logging.info('init rabbitmq')
        engine = _Engine(lambda :pika.BlockingConnection(pika.ConnectionParameters(**params)))
    except:
        logging.error('can not init rabbitmq')
        
        
class _connection(object):
    def __init__(self):
        self.connection = None
        
    def channel(self):
        global engine
        if self.connection is None:
            logging.info('open connection of queue')
            self.connection = engine.connect()
            
        return self.connection.channel()
    
    def cleanup(self):
        connection = self.connection
        if connection:
            self.connection = None
            connection.close()
        
class _MqCtx(threading.local):
    def __init__(self):
        self.connection = None
        
    def isinit(self):
        return not self.connection is None
    
    def init(self):
        self.connection = _connection()
        
    def cleanup(self):
        self.connection.cleanup()
        self.connection = None
        
_mq_ctx = _MqCtx()

class Queue(object):
    def __init__(self, qn, rk):
        global _mq_ctx
        if not _mq_ctx.isinit():
            _mq_ctx.init()
        self.qn = qn
        self.rk = rk
        channel = _mq_ctx.connection.channel()
        channel.queue_declare(queue=qn,durable=True)
        channel.exchange_declare(exchange='direct_logs', type='direct')
        channel.queue_bind(exchange='direct_logs',
                           queue=qn,
                           routing_key=rk)
        self.channel = channel
        
    def __del__(self):
        if _mq_ctx:
            _mq_ctx.cleanup()    
           
def send(msg,queue):
    queue.channel.basic_publish(exchange='direct_logs',
                          routing_key=queue.rk,
                          body=msg)
    
    logging.info(' [p] %r:%r' % (queue.rk,msg))
    #print ' [p] %r:%r' % (queue.rk,msg)
    
    
def receive(queue,callback):
    logging.info('Waiting for logs.')

    
    queue.channel.basic_consume(callback, queue=queue.qn,)    
    queue.channel.start_consuming()
        

if __name__=='__main__':
    from WindowsWatcher import WinWatcher
    import json
    logging.basicConfig(level=logging.INFO)
    create_engine()
    agent = WinWatcher()
    
    class sender(threading.Thread):
        def __init__(self):
            super(sender,self).__init__()
            self.queue = Queue('test', 'test')
        def run(self):
            while True:
                msg = agent.cpu_use()
                self.queue.send(json.dumps(msg))
            
    class receiver(threading.Thread):
        def __init__(self):
            super(receiver,self).__init__()
            self.queue = Queue('test', 'test')
        def run(self):
            receive(self.queue,callback)
                    
    #t = sender()
    #t.start()
    p = receiver()
    p.start()    