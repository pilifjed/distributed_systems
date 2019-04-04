import pika
import sys
import threading


def callback(ch, method, properties, body):
    if 'admin info' in method.routing_key:
        print("[ADMIN INFO]: " + body.decode('UTF-8'))
    else:
        print("[TECHNICIAN REPORT]: Examination of " + body.decode('UTF-8'))


def thread_fun():
    connection1 = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel1 = connection1.channel()
    channel1.exchange_declare(exchange='doctor_exchange', exchange_type='topic')
    result1 = channel1.queue_declare('', exclusive=True)
    queue_name1 = result1.method.queue
    channel1.queue_bind(queue=queue_name1, exchange='doctor_exchange', routing_key=doctor_name + '.#')
    channel1.queue_bind(queue=queue_name1, exchange='info_exchange')
    channel1.basic_consume(queue=queue_name1, on_message_callback=callback, auto_ack=True)
    channel1.start_consuming()


if len(sys.argv) != 2:
    sys.stderr.write("Please specify proper run parameters\n")
doctor_name = sys.argv[1]

threading1 = threading.Thread(target=thread_fun)
threading1.daemon = True
threading1.start()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()
channel.exchange_declare(exchange='request_exchange', exchange_type='topic')

print('You are currently using ' + doctor_name + '\'s client.\nPlease enter examination_type and patient_name:')

text = ''
while 'disconnect' not in text:
    text = input()
    split = text.split(sep=' ', maxsplit=1)
    if len(split) == 2:
        examination_type, patient_name = split
        routing_key = doctor_name + '.' + examination_type
        wrapped_message = bytes(patient_name, encoding='UTF-8')
        channel.basic_publish(exchange='request_exchange', routing_key=routing_key, body=wrapped_message)
connection.close()
