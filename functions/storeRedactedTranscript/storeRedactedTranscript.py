import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOGGING_LEVEL"]))

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')

def split_s3_path(s3_path):
    path_parts=s3_path.replace("s3://","").split("/")
    bucket=path_parts.pop(0)
    key="/".join(path_parts)
    return bucket, key

def lambda_handler(event,context):
    try:
        logger.info('Event: {}'.format(event))
        # Download original transcript file
        source_bucket = event.get('source_bucket')
        source_key = event.get('source_key')
        source_backup_key = event.get('source_key') + '.backup'
        redacted_content_bucket, redacted_content_key = split_s3_path(event.get('ComprehendJob').get('OutputDataConfig').get('S3Uri'))
        redaction_source_key = event.get('LoadTranscript').get('redaction_source_key')
        
        # Construct filename of redaction output
        redacted_content_out_key = redacted_content_key + event.get('ComprehendJob').get('InputDataConfig').get('S3Uri').split('/')[-1] + '.out'
        source_content_obj = s3_resource.Object(source_bucket, source_backup_key)
        source_content = json.loads(source_content_obj.get()['Body'].read().decode('utf-8'))
        
        s3_source_metadata = event.get('source_metadata')
        
        # Create transcript object
        pii_transcript = {
            "Version": source_content.get("Version"),
            "AWSAccountId": source_content.get("AWSAccountId"),
            "InstanceId": source_content.get("InstanceId"),
            "InitialContactId": source_content.get("InitialContactId"),
            "ContactId": source_content.get("ContactId"),
            "Participants": source_content.get("Participants"),
            "Transcript": []
        }
        
        # Get redacted content 
        redacted_content_obj = s3_resource.Object(redacted_content_bucket, redacted_content_out_key)
        redacted_content = json.loads(redacted_content_obj.get()['Body'].read().decode('utf-8')).get('Content')

        # Replace original transcript content if its plain/text with redacted content
        for transcript in source_content.get('Transcript'):
            pii_item = transcript
            if(transcript.get('ContentType') == 'text/plain'):
                #Replace transcript content with redacted content
                pii_item['Content'] = redacted_content.pop(0)
            pii_transcript.get("Transcript").append(pii_item)
        
        # add state to metadata
        s3_source_metadata['state'] = 'redacted'

        # Upload S3 transcript object with redacted transcript
        s3_client.put_object(
            Bucket=source_bucket,
            Key=source_key,
            Body=json.dumps(pii_transcript),
            Metadata=s3_source_metadata
        )
        
        # Clean up unwanted files
        s3_resource.Object(source_bucket, redacted_content_out_key).delete()
        s3_resource.Object(source_bucket, redacted_content_key + '.write_access_check_file.temp').delete()
        s3_resource.Object(source_bucket, redaction_source_key).delete()
        
        return "Successfully redacted transcripts!"
    except Exception as e:
        logger.error('Error: {}'.format(e))