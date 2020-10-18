import json
import boto3
import os
from dotenv import load_dotenv
import uuid
load_dotenv()
access_key = os.getenv('AWS_ACCESS_KEY')
secret_key = os.getenv('AWS_SECRET_KEY')
region = os.getenv('AWS_REGION')
sns_arn=os.getenv('SNS_TOPIC_ARN')

class Notification:
    def __init__(self, topic, payload):
        self.topic = topic
        self.topic_arn = sns_arn + topic
        self.payload = payload
        self.event_id = uuid.uuid1()
        self.payload['notification_id'] = str(self.event_id)
        self.client = boto3.client('sns',
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key,
                              region_name=region)

    def send(self):
        response = self.client.publish(
            TargetArn=self.topic_arn,
            Message=json.dumps({'default': json.dumps(self.payload)}),
            MessageStructure='json'
        )
        return {'response' : response}


class Queue:
    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.client = boto3.client('sqs',
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key,
                              region_name=region)
        self.queue_url = self.client.get_queue_url(
            QueueName=queue_name)['QueueUrl']

    def get_messages(self):
        while True:
            resp = self.client.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=['All'],
                MaxNumberOfMessages=1
            )

            try:
                yield from resp['Messages']
            except KeyError:
                return

            entries = [
                {'Id': msg['MessageId'], 'ReceiptHandle': msg['ReceiptHandle']}
                for msg in resp['Messages']
            ]

            resp = self.client.delete_message_batch(
                QueueUrl=self.queue_url, Entries=entries
            )

            if len(resp['Successful']) != len(entries):
                raise RuntimeError(
                    f"Failed to delete messages: entries={entries!r} resp={resp!r}"
                )


if __name__ == '__main__':
    plexq = Queue('plex_queue')
    for i in plexq.get_messages():
        print(i)
        break
