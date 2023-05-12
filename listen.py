import os
import pika
import json

from start import start_brute

QUEUE_NAME_TASK = os.environ.get('QUEUE_NAME_TASK') \
    if os.environ.get('QUEUE_NAME_TASK') \
    else 'rtsp_brute_task'
QUEUE_NAME_RESULT = os.environ.get('QUEUE_NAME_RESULT') \
    if os.environ.get('QUEUE_NAME_RESULT') \
    else 'rtsp_brute_result'
RABBITMQ_URL = os.environ.get('RABBITMQ_URL') \
    if os.environ.get('RABBITMQ_URL') \
    else 'localhost'


class Task:
    def __init__(self, task_id, targets, save_screenshots):
        self.task_id = task_id
        self.targets = targets
        self.save_screenshots = save_screenshots

    def to_json(self):
        return json.dumps({'task_id': self.task_id, 'targets': self.targets})

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(data['task_id'], data['targets'], data['screenshots'])


class Worker:
    def __init__(self, rabbitmq_url, task_queue, result_queue):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=task_queue, durable=True)
        self.channel.queue_declare(queue=result_queue, durable=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=task_queue, on_message_callback=self.handle_task)

    def handle_task(self, ch, method, props, body):
        task = Task.from_json(body.decode('utf-8'))
        result = self.process_task(task)

        ch.basic_publish(
            exchange='',
            routing_key=self.result_queue,
            properties=pika.BasicProperties(
                delivery_mode=2
            ),
            body=json.dumps(result)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def process_task(self, task):
        try:
            targets = []
            for t in task.targets:
                for port in t['ports']:
                    targets.append({'host': t['host'], 'port': port})

            brute_res = start_brute(
                brute_id=task.task_id,
                targets=targets,
                return_full_result=True,
                save_screenshots_to_db=task.save_screenshots
            )
            return {'task_id': task.task_id, 'result': brute_res}
        except Exception as e:
            print(str(e))
            return {'task_id': task.task_id, 'error': str(e)}

    def start(self):
        self.channel.start_consuming()


if __name__ == '__main__':
    worker = Worker(RABBITMQ_URL, QUEUE_NAME_TASK, QUEUE_NAME_RESULT)
    worker.start()