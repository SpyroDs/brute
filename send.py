import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='rtsp_brute')

body = '{"brute_id": "00955aab-eb53-4f6a-803f-fa9a9f1cc3d7", "targets": [' \
       '{"host": "host1", "ports": [554,1654]},' \
       '{"host": "host2", "ports": [554,10554]},' \
       '{"host": "host3", "ports": [554]}' \
       ']}'

channel.basic_publish(exchange='', routing_key='rtsp_brute', body=str(body))
print(" [x] Sent " + body)
connection.close()