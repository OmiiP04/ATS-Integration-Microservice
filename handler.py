import json
import logging
from ats_client import GreenhouseClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ats_client = GreenhouseClient()

def _response(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    }

def get_jobs(event, context):
    logger.info("Received get_jobs request")
    try:
        jobs = ats_client.get_jobs()
        return _response(200, jobs)
    except Exception as e:
        logger.error(f"Error in get_jobs: {str(e)}")
        return _response(500, {"error": str(e)})

def create_candidate(event, context):
    logger.info("Received create_candidate request")
    try:
        if not event.get('body'):
            return _response(400, {"error": "Missing request body"})
            
        payload = json.loads(event.get('body'))
        # Basic validation
        required_fields = ['name', 'email', 'job_id']
        for field in required_fields:
            if field not in payload:
                return _response(400, {"error": f"Missing required field: {field}"})

        result = ats_client.create_candidate(payload)
        return _response(201, result)
    except Exception as e:
        logger.error(f"Error in create_candidate: {str(e)}")
        return _response(500, {"error": str(e)})

def get_applications(event, context):
    logger.info("Received get_applications request")
    try:
        # Check query parameters
        params = event.get('queryStringParameters') or {}
        job_id = params.get('job_id')
        
        if not job_id:
            return _response(400, {"error": "Missing required query parameter: job_id"})

        applications = ats_client.get_applications(job_id)
        return _response(200, applications)
    except Exception as e:
        logger.error(f"Error in get_applications: {str(e)}")
        return _response(500, {"error": str(e)})
