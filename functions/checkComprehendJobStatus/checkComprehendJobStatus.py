import boto3
import datetime
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOGGING_LEVEL"]))

comprehend_client = boto3.client('comprehend')

def lambda_handler(event,context):
    try:
        logger.info('Event: {}'.format(event))
        response = comprehend_client.describe_pii_entities_detection_job(
            JobId=event.get('JobId')
        )
         # BELOW IS THE CODE TO FIX SERIALIZATION ON DATETIME OBJECTS
        if "SubmitTime" in response.get("PiiEntitiesDetectionJobProperties"):
            job_submit_time = response.get("PiiEntitiesDetectionJobProperties").get("SubmitTime")
            response["PiiEntitiesDetectionJobProperties"]["SubmitTime"] = job_submit_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z") if isinstance(job_submit_time, datetime.datetime) else str(job_submit_time)
        if "EndTime" in response.get("PiiEntitiesDetectionJobProperties"):
            job_end_time = response.get("PiiEntitiesDetectionJobProperties").get("EndTime")
            response["PiiEntitiesDetectionJobProperties"]["EndTime"] = job_end_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z") if isinstance(job_end_time, datetime.datetime) else str(job_end_time)
        return response.get('PiiEntitiesDetectionJobProperties')
    except Exception as e:
        logger.error('Error: {}'.format(e))