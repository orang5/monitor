import pika, json
from WindowsWatcher import WinWatcher
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='www',durable=True)

channel.exchange_declare(exchange='direct_logs',
                         type='direct')

agent = WinWatcher()
while True:
    msg = json.dumps(agent.cpu_use())
    channel.basic_publish(exchange='direct_logs',
                          routing_key='www',
                          body='hello')
    print msg

'''
channel.exchange_declare(exchange='direct_logs',
                         type='direct')

severity = 'error'
message = 'Hello World!'
channel.basic_publish(exchange='direct_logs',
                      routing_key=severity,
                      body=message)
channel.basic_publish(exchange='direct_logs',
                      routing_key='warning',
                      body=message)
channel.basic_publish(exchange='direct_logs',
                      routing_key='warning',
                      body=message)
print " [x] Sent %r:%r" % (severity, message)
'''
connection.close()