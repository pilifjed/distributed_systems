import pika
import threading
from datetime import datetime


def callback(ch, method, properties, body):
    current_time = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    print(current_time + ": " + method.routing_key + " - " + body.decode('UTF-8'))


def thread_fun():
    connection1 = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel1 = connection1.channel()
    channel1.exchange_declare(exchange='request_exchange', exchange_type='topic')
    channel1.exchange_declare(exchange='doctor_exchange', exchange_type='topic')
    result1 = channel1.queue_declare('', exclusive=True)
    queue_name1 = result1.method.queue
    channel1.queue_bind(queue=queue_name1, exchange='request_exchange', routing_key='#')
    channel1.queue_bind(queue=queue_name1, exchange='doctor_exchange', routing_key='#')
    channel1.basic_consume(queue=queue_name1, on_message_callback=callback, auto_ack=True)
    channel1.start_consuming()


threading1 = threading.Thread(target=thread_fun)
threading1.daemon = True
threading1.start()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()
channel.exchange_declare(exchange='info_exchange', exchange_type='fanout')

print('You are currently using admin console, if you got access in unauthorised way, please don\'t hack.')

text = ''
while 'disconnect' not in text:
    text = input()
    routing_key = 'admin info'
    wrapped_message = bytes(text, encoding='UTF-8')
    # print(routing_key + " : " + wrapped_message.decode('UTF-8'))
    channel.basic_publish(exchange='info_exchange', routing_key=routing_key, body=wrapped_message)
connection.close()
