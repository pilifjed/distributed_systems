import pika
import sys
import random
import time


def handle_info(ch, method, properties, body):
    print("[ADMIN INFO]: " + body.decode('UTF-8'))


def callback(ch, method, properties, body):
    message = body.decode('UTF-8')
    routing_info = method.routing_key
    examination_type = routing_info.split('.')[1]  # Could be done better but I don't care
    print("[DOCTOR REQUEST]: Please examine " + message + "\'s " + examination_type )
    wrapped_message = bytes(message + ' ' + examination_type + ' done', encoding='UTF-8')
    time.sleep(random.randint(1, 20))
    channel.basic_publish(exchange='doctor_exchange', routing_key=routing_info, body=wrapped_message)


if len(sys.argv) != 3:
    sys.stderr.write("Please specify proper run parameters\n")
queue_1_name = sys.argv[1]
queue_2_name = sys.argv[2]

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

channel.exchange_declare(exchange='request_exchange', exchange_type='topic')
channel.exchange_declare(exchange='doctor_exchange', exchange_type='topic')
channel.queue_declare(queue=queue_1_name)
channel.queue_declare(queue=queue_2_name)
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(queue=queue_name, exchange='info_exchange')
channel.queue_bind(queue=queue_1_name, exchange='request_exchange', routing_key='#.' + queue_1_name)
channel.queue_bind(queue=queue_2_name, exchange='request_exchange', routing_key='#.' + queue_2_name)
channel.basic_consume(queue=queue_name, on_message_callback=handle_info, auto_ack=True)
channel.basic_consume(queue=queue_1_name, on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue=queue_2_name, on_message_callback=callback, auto_ack=True)

print('Technician starts working on ' + queue_1_name + "\'s and " + queue_2_name + "\'s")
channel.start_consuming()
