import logging, threading, functools

class _Engine(object):
    def __init__(self,connect):
        self.connect = connect
        
    def connect(self):
        return self.connect
    
engine = None

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
            logging.info('open connection if queue')
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


    
class _connectionCtx(object):
    def __enter__(self):
        global _mq_ctx
        self.should_cleanup = False
        if not _mq_ctx.isinit():
            _mq_ctx.init()
            self.should_cleanup = True
        return self
            
    def __exit__(self, exctype, excvalue, traceback):
        global _mq_ctx
        if self.should_cleanup:
            _mq_ctx.cleanup()
            
def connection():
    return _connectionCtx()

def with_connection(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with connection():
            return func(*args, **kw)
    return _wrapper        



#@with_connection        
#def send(rk, msg, qn = 'work'):
    #global _mq_ctx
    #channel = _mq_ctx.connection.channel()
    #channel.queue_declare(queue=qn,durable=True)
    #channel.exchange_declare(exchange='direct_logs',
                             #type='direct')    
    #channel.basic_publish(exchange='direct_logs',
                          #routing_key=rk,
                          #body=msg)
    #logging.info(' [p] %r:%r' % (rk,msg))
    #print ' [p] %r:%r' % (rk,msg)
        
#@with_connection
#def receive(rk, qn = 'work'):
    #global _mq_ctx
    #channel = _mq_ctx.connection.channel()    
    #channel.queue_declare(queue=qn,durable=True)
    #channel.queue_bind(exchange='direct_logs',
                       #queue=qn,
                       #routing_key=rk)
    #logging.info('Waiting for logs.')
    
    #def callback(ch, method, properties, body):
        #'saver'
        #logging.info(" [x] %r:%r" % (method.routing_key, body,))
        #print " [x] %r:%r" % (method.routing_key, body,)
        #ch.basic_ack(delivery_tag = method.delivery_tag)
    
    #channel.basic_consume(callback, queue=qn,)    
    #channel.start_consuming()    
    
class Queue(object):
        
    @staticmethod
    @with_connection
    def send(msg, qn, rk):
        global _mq_ctx
        channel = _mq_ctx.connection.channel()
        channel.queue_declare(queue=qn,durable=True)
        channel.exchange_declare(exchange='direct_logs',
                                 type='direct')

        channel.basic_publish(exchange='direct_logs',
                              routing_key=rk,
                              body=msg)
        
        logging.info(' [p] %r:%r' % (rk,msg))
        print ' [p] %r:%r' % (rk,msg)
        
    @staticmethod    
    @with_connection
    def receive(qn,rk):
        global _mq_ctx
        channel = _mq_ctx.connection.channel()    
        channel.queue_declare(queue=qn,durable=True)
        channel.queue_bind(exchange='direct_logs',
                           queue=qn,
                           routing_key=rk)
        logging.info('Waiting for logs.')
        
        def callback(ch, method, properties, body):
            'saver'
            logging.info(" [x] %r:%r" % (method.routing_key, body,))
            print " [x] %r:%r" % (method.routing_key, body,)
            ch.basic_ack(delivery_tag = method.delivery_tag)
        
        channel.basic_consume(callback, queue=qn,)    
        channel.start_consuming()
    
class TestQueue(Queue):
    @staticmethod
    def send(msg):
        super(TestQueue,TestQueue).send(msg,'test','test')
        
    @staticmethod
    def receive():
        super(TestQueue,TestQueue).receive('test','test')
        
        
        
class WorkQueue(Queue):
    @staticmethod
    def send(cls, msg):
        super(WorkQueue,WorkQueue).send(msg,'work','work')
        
    @staticmethod
    def receive(cls):
        super(WorkQueue,WorkQueue).receive('work','work')

if __name__=='__main__':
    from WindowsWatcher import WinWatcher
    import json
    create_engine()
    agent = WinWatcher()
    
    class sender(threading.Thread):
        def __init__(self):
            super(sender,self).__init__()
        def run(self):
            TestQueue.send('fadf')
            
    class receiver(threading.Thread):
        def __init__(self):
            super(receiver,self).__init__()
        def run(self):
            TestQueue.receive()
                    
    t = sender()
    t.start()
    p = receiver()
    p.start()    