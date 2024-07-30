import io
import os
import json
import sys
import logging
import oci
from fdk import response

import oci.object_storage
from base64 import b64encode, b64decode

def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        bucketName  = body["data"]["additionalDetails"]["bucketName"]
        objectName  = body["data"]["resourceName"]

    except Exception:
        error = 'Input a JSON object in the format: \'{"bucketName": "<bucket name>"}, "objectName": "<object name>"}\' '
        raise Exception(error)
    
    if not objectName.lower().endswith(('.aac', '.ac3', '.amr', '.au', '.flac', '.m4a', '.mkv', '.mp3', '.mp4', '.oga', '.ogg', '.wav', '.webm')):
        # If the extension is not found, don't run the transcription job
        return response.Response(ctx, response_data='Invalid file format. Only AAC, AC3, AMR, AU, FLAC, M4A, MKV, MP3, MP4, OGA, OGG, WAV, WEBM are supported.', headers={'Content-Type': 'application/json'})
    
    # resp = get_object(bucketName, objectName)
    signer = oci.auth.signers.get_resource_principals_signer()
    ai_client = oci.ai_speech.AIServiceSpeechClient(config={}, signer=signer)
    transcription_job_details = {
        "compartment_id": "<COMPARTMENT_OCID>",
        "model_details": oci.ai_speech.models.TranscriptionModelDetails(
            model_type="WHISPER_MEDIUM",
            domain="GENERIC",
            language_code='en',
            transcription_settings=oci.ai_speech.models.TranscriptionSettings(
                diarization=oci.ai_speech.models.Diarization(is_diarization_enabled=True)
            )
        ),
        "input_location": oci.ai_speech.models.ObjectListInlineInputLocation(
            location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
            object_locations=[oci.ai_speech.models.ObjectLocation(
                namespace_name="<NAMESPACE>",
                bucket_name="<BUCKET_NAME>",
                object_names=[objectName]
            )]
        ),
        "output_location": oci.ai_speech.models.OutputLocation(
            namespace_name="<NAMESPACE>",
            bucket_name="<OUTPUT_BUCKET_NAME>",
            prefix="Transcript"
        )
    }
    
    create_transcription_job_response = ai_client.create_transcription_job(create_transcription_job_details=oci.ai_speech.models.CreateTranscriptionJobDetails(**transcription_job_details))
    logging.getLogger().info('AI Speech Response: ' + str(create_transcription_job_response.data))

    return response.Response(
        ctx,
        response_data=create_transcription_job_response.data,
        headers={"Content-Type": "application/json"}
    )