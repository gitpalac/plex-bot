import json
import boto3
import os
from dotenv import load_dotenv
import uuid

load_dotenv()
access_key = os.getenv('AWS_ACCESS_KEY')
secret_key = os.getenv('AWS_SECRET_KEY')
region = os.getenv('AWS_REGION')
topic_arn=os.getenv('SNS_TOPIC_ARN')

class Notification:
    def __init__(self, payload):
        self.payload = payload
        self.content_type = payload.get('content_type', None)
        self.keywords = payload.get('keywords', None)
        self.event_id = uuid.uuid1()
        self.payload['event_id'] = self.event_id

    def send(self):
        client = boto3.client('sns',
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key,
                              region_name=region)
        response = client.publish(
            TargetArn=topic_arn,
            Message=json.dumps({'default': json.dumps(self.payload)}),
            MessageStructure='json'
        )
        print(response)


if __name__ == '__main__':
    Notification()