import json
from flask import Flask
from flask import request
import aws_lambda_wsgi
import boto3
from boto3.dynamodb.conditions import Key, Attr
import template
import config
import pdb

app = Flask(__name__)
@app.route('/create_table', methods = ["GET"])
def table_creation():
    queryparams = request.args
    if 'tablename' in queryparams:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName = 'device_registry',
            KeySchema = [
                {
                    'AttributeName': 'sn',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'token',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions = [
                {
                    'AttributeName': 'sn',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'token',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput = {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='device_registry')
        template.API_response["statuscode"] = 200
        template.API_response["message"] = "Table created successfully. Total items in table are {}".format(table.item_count)
    else:
        template.API_response["statuscode"] = 405
        template.API_response["message"] = "Table Name not specified"
    return template.API_response

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

@app.route('/testing', methods = ["GET"])
def testing():
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


@app.route('/device_registration', methods=["GET"])
def device_registration():
    pdb.set_trace()
    template.API_response['data'] = {}
    template.API_response['message'] = "No data present at this endpoint"
    template.API_response['statuscode'] = 200
    queryparams = request.args
    device_registry_table = 'device_registry'
    if 'sn' in queryparams and 'token' in queryparams:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(device_registry_table)
        device_query = table.get_item(Key={
            'sn': queryparams['sn'],
            'token': queryparams['token']
        })
        if 'Item' in device_query:
            if 'certid' not in device_query['Item']:
                new_thing = boto3.client('iot')
                new_thing_response = new_thing.create_thing(
                    thingName=queryparams['sn'],
                    thingTypeName='IOT_Thing',
                    attributePayload={
                        'attributes': {
                            'sn': queryparams['sn']
                        },
                        'merge': True
                    })
                if 'thingArn' in new_thing_response:
                    new_thing_certs = new_thing.create_keys_and_certificate(
                        setAsActive=True)
                    attach_policy = new_thing.attach_principal_policy(
                        policyName=config.Device_Policy,
                        principal=new_thing_certs['certificateArn'])
                    attach_certs_tothing = new_thing.attach_thing_principal(
                        thingName=new_thing_response["thingName"],
                        principal=new_thing_certs['certificateArn'])
                    device_update = table.update_item(
                        TableName=device_registry_table,
                        Key={
                            'sn': queryparams['sn'],
                            'token': queryparams['token']
                        },
                        UpdateExpression="set certarn = :carn, certid = :cid, certpem = :cpem, publickey = :puk, privatekey = :prk, awshost = :ah, rootca = :rca",
                        ExpressionAttributeValues={
                            ':carn' : new_thing_certs['certificateArn'],
                            ':cid'  : new_thing_certs['certificateId'],
                            ':cpem' : new_thing_certs['certificatePem'],
                            ':puk'  : new_thing_certs['keyPair']['PublicKey'],
                            ':prk'  : new_thing_certs['keyPair']['PrivateKey'],
                            ':ah'   : config.awshost,
                            ':rca'  : config.rootca
                        })
                    if device_update["ResponseMetadata"]["HTTPStatusCode"] == 200:
                        template.API_response["message"] = "Successfully created the thing in AWS"
                        template.API_response["data"]["awshost"] = config.awshost
                        template.API_response["data"]["rootca"] = config.rootca
                        template.API_response["data"]["privatekey"] = new_thing_certs['keyPair']['PrivateKey']
                        template.API_response["data"]["certpem"] = new_thing_certs['certificatePem'] 
                        template.API_response["statuscode"] = 200
                    else:
                        template.API_response["message"] = "Thing creation failed"
                        template.API_response["statuscode"] = 200
                else:
                    template.API_response["message"] = "Thing creation failed at IOT Core"
                    template.API_response["statuscode"] = 200
            else:
                template.API_response["message"] = "Thing already has certificates attached to it"
                template.API_response["statuscode"] = 200
        else:
            template.API_response["message"] = "Device with the respective Serial Number and Token not found in DB"
            template.API_response["statuscode"] = 200

    else:
        template.API_response["statuscode"] = 405
        template.API_response["message"] = "No serial number and token present"

    return template.API_response

@app.route('/sample', methods = ["GET"])
def sample_function():
    return True


def handler(event, context):
    return aws_lambda_wsgi.response(app, event, context)

if __name__ == "__main__":
    app.run()