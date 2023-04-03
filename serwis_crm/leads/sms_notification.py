import json
import logging
import time
import boto3
from botocore.exceptions import ClientError, NoRegionError
from flask import Flask

app = Flask(__name__)

class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""
    def __init__(self, sns_resource):
        """
        :param sns_resource: A Boto3 Amazon SNS resource.
        """
        self.sns_resource = sns_resource

    def publish_text_message(self, phone_number, message):
        """
        Publishes a text message directly to a phone number without need for a
        subscription.

        :param phone_number: The phone number that receives the message. This must be
                             in E.164 format. For example, a United States phone
                             number might be +12065550101.
        :param message: The message to send.
        :return: The ID of the message.
        """
        try:
            sender_id="CraftBike"
            msg_attrs={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': sender_id
                    }
                }
            response = self.sns_resource.meta.client.publish(
                PhoneNumber=phone_number, Message=message, MessageAttributes=msg_attrs)
            message_id = response['MessageId']
            app.logger.info("Published message to %s.", phone_number)
        except ClientError or NoRegionError:
            app.logger.error("Couldn't publish message to %s.", phone_number)
            raise
        else:
            return message_id