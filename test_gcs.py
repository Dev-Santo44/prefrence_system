import os
import json
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
GS_CREDENTIALS_JSON = os.getenv("GS_CREDENTIALS_JSON")

if GS_BUCKET_NAME and GS_CREDENTIALS_JSON:
    try:
        cred_dict = json.loads(GS_CREDENTIALS_JSON.strip("'"))
        client = storage.Client.from_service_account_info(cred_dict)
        bucket = client.bucket(GS_BUCKET_NAME)
        # Try to list one object to verify access
        blobs = list(bucket.list_blobs(max_results=1))
        print(f"Connected to bucket: {GS_BUCKET_NAME}")
        print(f"Sample blob: {blobs[0].name if blobs else 'No blobs found'}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Missing GCS credentials in .env")
