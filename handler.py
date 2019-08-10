import json
from flask import Flask
from flask import request
import aws_lambda_wsgi

app = Flask(__name__)
@app.route('/device_registration', methods = ["GET"])
def device_registration():
    return request.query_string

@app.route('/v1/security', methods = ["GET"])
def security():
    return "security"

def handler(event, context):
    return aws_lambda_wsgi.response(app, event, context)