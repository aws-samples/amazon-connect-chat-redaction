import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOGGING_LEVEL"]))

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        logger.info('Event: {}'.format(event))
        source_bucket = event.get("source_bucket")
        source_key = event.get("source_key")
        dest_bucket = source_bucket
        dest_key = source_key
        
         # get transcript & metadata from S3 object
        transcript_s3_object = s3_resource.Object(source_bucket, source_key)
        transcript = json.loads(transcript_s3_object.get()['Body'].read().decode('utf-8'))
        
        # Create backup of original transcript
        s3_client.copy_object(Bucket=source_bucket,Key=source_key+'.backup',CopySource=source_bucket+'/'+source_key)
        
        # load each transcript item that needs to be redacted in an array
        transcript_content = {'Content':[]}
        for item in transcript.get("Transcript"):
            if (item.get("ContentType") == "text/plain"):
                transcript_content.get('Content').append(item.get("Content"))
        
        # upload content array to be redacted
        redaction_source_key = source_key + '.redaction_source'
        redaction_source_object = s3_resource.Object(source_bucket, redaction_source_key)
        redaction_source_object.put(Body=json.dumps(transcript_content))
        
        # Delete source transcript to remove Connect UI access to unredacted transcripts
        s3_resource.Object(source_bucket,source_key).delete()
        
        step_function_output = {
            "redaction_source_key": redaction_source_key,
            "destination_bucket": dest_bucket,
            "destination_key": dest_key,
        }
        return step_function_output
    except Exception as e:
        logger.error('Error: {}'.format(e))