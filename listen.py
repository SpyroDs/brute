import pika
import json

from start import start_brute

QUEUE_NAME = 'rtsp_brute'


def callback(ch, method, properties, body):
    try:
        print(body)
        loaded = json.loads(body.decode('utf-8'))
        targets = []
        for t in loaded['targets']:
            for port in t['ports']:
                targets.append({'host': t['host'], 'port': port})

        result = start_brute(loaded['brute_id'], targets)
        print(json.dumps({
            "brute_id": loaded['brute_id'],
            "results": result,
        }))
    except Exception as e:
        print(str(e))


connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
print(" [*] Waiting for messages. To exit press Ctrl+C")
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
