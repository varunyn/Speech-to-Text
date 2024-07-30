import json
import sys
import oci
import io
import oci
from fdk import response
import os

def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        bucketName  = body["data"]["additionalDetails"]["bucketName"]
        objectName  = body["data"]["resourceName"]
    except Exception:
        error = 'Input a JSON object in the format: \'{"bucketName": "<bucket name>"}, "objectName": "<object name>"}\' '
        raise Exception(error)
    resp = get_object(bucketName, objectName)
    uploadObjectResponse = uploadObject(bucketName,objectName,resp)

    return response.Response(
        ctx,
        response_data=uploadObjectResponse,
        headers={"Content-Type": "application/json"}
    )

def get_object(bucketName, objectName):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    namespace = client.get_namespace().data
    try:
        print("Searching for bucket and object", flush=True)
        object = client.get_object(namespace, bucketName, objectName)
        print("found object", flush=True)
        if object.status == 200:
            # print("Success: The object " + objectName + " was retrieved with the content: " + object.data.text, flush=True)
            message = get_transcript(json.loads(object.data.text))
        else:
            message = "Failed: The object " + objectName + " could not be retrieved."
    except Exception as e:
        message = "Failed: " + str(e.message)
    return message

def get_transcript(data):
    json_data = data["transcriptions"][0]["tokens"]
    # Get First Speaker and StartTime
    current_speaker = json_data[0].get("speakerIndex")
    start_time = json_data[0].get("startTime")
    end_time = None
    token_count = 0
    conversation = ""
    complete_conversation = ""

    for token in json_data:
        speaker_index = token.get("speakerIndex")
        token_value = token.get("token")

        if speaker_index != current_speaker:
            if token_count != 0:
                complete_conversation += f"\nSpeaker {speaker_index}: {convert_time(start_time)} - {convert_time(end_time)}"
                complete_conversation += conversation
                complete_conversation += "\n"

            conversation = ""            
            start_time = token.get("startTime")
            conversation += f"{token_value}"
            current_speaker = speaker_index
        else:
            if token_count == 0: # first token only
                conversation += f"{token_value}"
            else:
                conversation += f" {token_value}"
            end_time = token.get("endTime")

        token_count += 1

        # Write out last saved speaked conversation
    complete_conversation += f"\nSpeaker {current_speaker}: {convert_time(start_time)} - {convert_time(end_time)}\n\t"
    complete_conversation += conversation
    complete_conversation += "\n"

    return complete_conversation

def convert_time(time_string):
    parts = time_string[:-1].split(':')
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + float(part)
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    seconds = int(seconds) % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def uploadObject(bucketName,objectName,body):
    input_file_name = os.path.basename(objectName).split(".")
    output_transcript = input_file_name[0] + "_transcript.txt"
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    try:
        put_object_response = client.put_object(
        namespace_name= client.get_namespace().data,
        bucket_name="<OUTPUT_BUCKET_NAME>",
        object_name=output_transcript,
        put_object_body=b"" + body.encode('utf-8')
        )
        message = "Transcript created successfully"
    except Exception as e:
        message = "Failed: " + str(e.message)
    return { "content": message }
