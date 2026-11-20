from flask import Flask, request, jsonify
from dotenv import load_dotenv
import json
import logging
import os
from handler import get_jobs, create_candidate, get_applications

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_context():
    class Context:
        def get_remaining_time_in_millis(self):
            return 30000
    return Context()

def lambda_event(body=None, query_params=None):
    return {
        "body": body,
        "queryStringParameters": query_params
    }

@app.route('/dev/jobs', methods=['GET'])
def route_get_jobs():
    event = lambda_event()
    context = lambda_context()
    response = get_jobs(event, context)
    return jsonify(json.loads(response['body'])), response['statusCode']

@app.route('/dev/candidates', methods=['POST'])
def route_create_candidate():
    body = request.data.decode('utf-8')
    event = lambda_event(body=body)
    context = lambda_context()
    response = create_candidate(event, context)
    return jsonify(json.loads(response['body'])), response['statusCode']


@app.route('/dev/applications', methods=['GET'])
def route_get_applications():
    query_params = request.args.to_dict()
    event = lambda_event(query_params=query_params)
    context = lambda_context()
    response = get_applications(event, context)
    return jsonify(json.loads(response['body'])), response['statusCode']

if __name__ == '__main__':
    print("Starting local runner on http://localhost:5000")
    app.run(debug=True, port=5000)
