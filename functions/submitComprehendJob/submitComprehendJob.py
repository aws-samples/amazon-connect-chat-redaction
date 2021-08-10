import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOGGING_LEVEL"]))

comprehend_client = boto3.client('comprehend')


def lambda_handler(event, context):
    try:
        logger.info('Event: {}'.format(event))
        input_s3_uri = 's3://' + \
            event.get('source_bucket') + '/' + \
            event.get('LoadTranscript').get('redaction_source_key')
        output_s3_uri = 's3://' + \
            event.get('source_bucket') + '/' + \
            event.get('source_key') + '.redactedoutput'
        language_code = event.get('language_code')
        pii_entity_types = os.environ["PII_ENTITY_TYPES"].split(",")
        mask_mode = os.environ["MASK_MODE"]
        # Submit Comprehend Job
        response = comprehend_client.start_pii_entities_detection_job(
            InputDataConfig={
                'S3Uri': input_s3_uri,
            },
            OutputDataConfig={
                'S3Uri': output_s3_uri,
            },
            Mode='ONLY_REDACTION',
            RedactionConfig={
                'PiiEntityTypes': pii_entity_types,
                'MaskMode': mask_mode,
            },
            DataAccessRoleArn=os.environ["COMPREHEND_DATA_ACCESS_ROLE_ARN"],
            JobName=event.get('jobName'),
            LanguageCode=language_code,
        )
        return {'JobId': response['JobId']}
    except Exception as e:
        logger.error('Error: {}'.format(e))
