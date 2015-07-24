# -*- coding: utf-8 -*-
import threading
import pika

class MQListener(threading.Thread):
    def __init__(self, channel, callback):
        threading.Thread.__init__(self)
        self.flag = False
        self.chn = channel
        self.callback = callback
        self.setDaemon(True)

    def run(self):
        print "MQListener start - ", self.name
        while not self.flag:
            self.chn.basic_consume()
        print "MQListener quit - ", self.name

class MQ:
    def __init__(self, host, port, username, password, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.args = kwargs
        self.conn = None
        self.channel = None

    def connect(self):
        params = dict(host=self.host, port=self.port,
                      credentials=pika.PlainCredentials(self.username, self.password),
                      # other options by default
                      virtual_host = None, channel_max=None,
                      frame_max=None,heartbeat_interval=None,ssl_options=None,
                      connection_attempts=None,retry_delay=None,socket_timeout=None,
                      locale=None,backpressure_detection=None)
        params.update(self.args)
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(**params))
        self.channel = self.conn.channel()
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.channel = None

    # use default channel to define exchange/queue
    def exchange_declare(**kwargs): self.channel.exchange_declare(**kwargs)
    def queue_declare(**kwargs): self.channel.queue_declare(**kwargs)
    def queue_bind(exc, q, rkey):
        self.channel.queue_bind(exchange=exc, queue=q, routing_key=rkey)

    def send(exc, rkey, msg):
        self.channel.basic_publish(exchange=exc, routing_key=rkey, body=msg)
