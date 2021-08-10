import json
import boto3
import os
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOGGING_LEVEL"]))

s3_client = boto3.client('s3')
sf_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    try:
        logger.info('Event: {}'.format(event))
        print(f'bucket: {event.get("Records")[0].get("s3").get("bucket").get("name")} / key: {event.get("Records")[0].get("s3").get("object").get("key")}')
        source_bucket = event.get("Records")[0].get("s3").get("bucket").get("name")
        source_key = event.get("Records")[0].get("s3").get("object").get("key").replace("%3A", ":")

        # get transcript & metadata from S3 object
        s3_object_metadata = s3_client.get_object(Bucket=source_bucket,Key=source_key).get('Metadata')

        # skip processing for backup file or redacted file
        if (source_key.endswith('.json') != True or s3_object_metadata.get('state') == 'redacted'):
            message = "Skipping redaction for file: {}/{} since it is a backup or already redacted.".format(source_bucket,source_key)
            logger.info(message)
            return message
        
        # Execute state machine if valid transcript file has triggered the function
        executeStateMachine(source_bucket,source_key,s3_object_metadata)
        return "Success"
    except Exception as e:
        logger.error('Error: {}'.format(e))

def executeStateMachine(source_bucket,source_key,s3_object_metadata):
    try:
        execution_input = {
          "jobName": s3_object_metadata.get('contact_id') +"_"+uuid.uuid4().hex,
          "wait_time": os.environ["WAIT_TIME"],
          "source_bucket": source_bucket,
          "source_key": source_key,
          "source_metadata": s3_object_metadata,
          "language_code": 'en',
        }
        logger.info('Starting Redaction State Machine: %s' % execution_input)
        response = sf_client.start_execution(
            stateMachineArn=os.environ['REDACTION_STATE_MACHINE_ARN'],
            input=json.dumps(execution_input)
        )
        logger.info('Redaction State Machine Response: {}'.format(response))
    except Exception as e:
        logger.error('Error: {}'.format(e))
        logger.error('Current data: {}'.format(execution_input))
