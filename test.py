import json
import pika


def process_result(a, b, c, body):
    print('====== Received result ========')
    print(body.decode('utf-8'))


task = {
    "task_id": "task_5",
    "screenshots": False,
    "targets": [
        {"host": "188.162.131.165", "ports": [554, 1654]}
    ]
}

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# Declare the queues
channel.queue_declare(queue='rtsp_brute_task', durable=True)
channel.queue_declare(queue='rtsp_brute_result', durable=True)
channel.basic_publish(exchange='',
                      routing_key='rtsp_brute_task',
                      body=json.dumps(task),
                      properties=pika.BasicProperties(
                          delivery_mode=2,  # make message persistent
                      ))
print("======== Send task =========")
print(json.dumps(task))
channel.basic_consume(queue='rtsp_brute_result', on_message_callback=process_result, auto_ack=True)

channel.start_consuming()

while True:
    pass
