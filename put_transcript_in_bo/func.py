import json
import sys
import oci
import io
import oci
from fdk import response
import os
import requests

def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        bucketName  = body["data"]["additionalDetails"]["bucketName"]
        objectName  = body["data"]["resourceName"]
    except Exception:
        error = 'Input a JSON object in the format: \'{"bucketName": "<bucket name>"}, "objectName": "<object name>"}\' '
        raise Exception(error)
 
    uploadObjectResponse = uploadObject(objectName=objectName)
    return response.Response(
        ctx,
        response_data=uploadObjectResponse,
        headers={"Content-Type": "application/json"}
    )


def extract_label(s):
    return s.replace('<REPLACE WITH NAMESPACE_MEDIA FILE BUCKET NAME>', '').replace('_transcript.txt', '')

def uploadObject(objectName):
    username = ''
    password = ''

    fileName= extract_label(objectName)

    get_file_url = "<REPLACE WITH BUSINESS OBJECT API>?q=fileName like '{}*'".format(fileName)
    response = requests.get(get_file_url,  auth=(username, password))
    data = json.loads(response.text)

    ids = []
    if not data.get('items'):
        print("No items found")
    else:
        for item in data['items']:
            ids.append(item['id'])

    url = "<REPLACE WITH BUSINESS OBJECT API>/{}".format(ids[0])

    body = {
        "transcriptPath": objectName
    }
    response = requests.patch(url, json=body,auth=(username, password))
    return response

