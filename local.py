import json
from flask import Flask
from flask import request
import aws_lambda_wsgi
import boto3

app = Flask(__name__)
@app.route('/device_registration', methods = ["GET"])
def device_registration():
    queryparams = request.args
    response = {
        "statuscode": 200,
        "message": ""
    }
    if 'sn' in queryparams.keys() and 'auth' in queryparams.keys():
        response["statuscode"] = 200
        response["message"] = "Success"
    else:
        response["statuscode"] = 200
        response["message"] = "Failure"
    return response

@app.route('/v1/s3buckets', methods = ["GET"])
def security():
    response = {
        "statuscode": 200,
        "message": ""
    }
    buckets={}
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
       buckets[bucket.name] = bucket.name
    return buckets


@app.route('/v1/device_shadow', methods = ["GET"])
def device_shadow():
    shadow = boto3.client('iot-data', region_name = 'us-west-2')
    response = shadow.get_thing_shadow(thingName = 'Raspberrypi')
    streamingBody = response["payload"]
    jsonState = json.loads(streamingBody.read())
    return jsonState


def handler(event, context):
    return aws_lambda_wsgi.response(app, event, context)

if __name__ == "__main__":
    app.run()
