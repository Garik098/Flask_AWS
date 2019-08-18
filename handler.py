import json
from flask import Flask
from flask import request
import aws_lambda_wsgi
import boto3
from boto3.dynamodb.conditions import Key, Attr
import template
import config

app = Flask(__name__)
@app.route('/device_registration', methods=['GET'])
def device_registration():
    template.API_response['data'] = {}
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
                        UpdateExpression='set certarn = :carn, certid = :cid, certpem = :cpem, publickey = :puk, privatekey = :prk, awshost = :ah, rootca = :rca',
                        ExpressionAttributeValues={
                            ':carn' : new_thing_certs['certificateArn'],
                            ':cid'  : new_thing_certs['certificateId'],
                            ':cpem' : new_thing_certs['certificatePem'],
                            ':puk'  : new_thing_certs['keyPair']['PublicKey'],
                            ':prk'  : new_thing_certs['keyPair']['PrivateKey'],
                            ':ah'   : config.awshost,
                            ':rca'  : config.rootca
                        })
                    if device_update['ResponseMetadata']['HTTPStatusCode'] == 200:
                        template.API_response['message'] = 'Successfully created the thing in AWS'
                        template.API_response['data']['awshost'] = config.awshost
                        template.API_response['data']['rootca'] = config.rootca
                        template.API_response['data']['privatekey'] = new_thing_certs['keyPair']['PrivateKey']
                        template.API_response['data']['certpem'] = new_thing_certs['certificatePem'] 
                        template.API_response['statuscode'] = 200
                    else:
                        template.API_response['message'] = 'Thing creation failed'
                        template.API_response['statuscode'] = 200
                else:
                    template.API_response['message'] = 'Thing creation failed at IOT Core'
                    template.API_response['statuscode'] = 200
            else:
                template.API_response['message'] = 'Thing already has certificates attached to it'
                template.API_response['statuscode'] = 200
        else:
            template.API_response['message'] = 'Device with the respective Serial Number and Token not found in DB'
            template.API_response['statuscode'] = 200

    else:
        template.API_response['statuscode'] = 405
        template.API_response['message'] = 'No serial number and token present'

    return template.API_response



def handler(event, context):
    return aws_lambda_wsgi.response(app, event, context)