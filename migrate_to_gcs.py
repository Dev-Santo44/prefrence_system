import os
import json
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv(override=True)

# ── GCS Configuration ────────────────────────────────────────────────────────
BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
PROJECT_ID = os.getenv("GS_PROJECT_ID")
CREDENTIALS_JSON = os.getenv("GS_CREDENTIALS_JSON")

def upload_media_to_gcs():
    if not all([BUCKET_NAME, PROJECT_ID, CREDENTIALS_JSON]):
        print("Error: GCS credentials (GS_BUCKET_NAME, GS_PROJECT_ID, GS_CREDENTIALS_JSON) missing in .env")
        return

    try:
        # Initialize GCS Client from JSON string
        from google.oauth2 import service_account
        cleaned_json = CREDENTIALS_JSON.strip("'")
        cred_dict = json.loads(cleaned_json)
        credentials = service_account.Credentials.from_service_account_info(cred_dict)
        client = storage.Client(project=PROJECT_ID, credentials=credentials)
        bucket = client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Failed to initialize GCS client: {e}")
        return

    media_root = r"d:\web\client\pranali\p_system\media"
    total_uploaded = 0

    print(f"Starting migration of {media_root} to GCS bucket: {BUCKET_NAME}...")

    for root, dirs, files in os.walk(media_root):
        for file in files:
            local_path = os.path.join(root, file)
            # Relative path for GCS object name (e.g., products/earrings/earring 1.jpg)
            relative_path = os.path.relpath(local_path, media_root).replace("\\", "/")
            
            try:
                # Determine Content-Type
                content_type = "image/jpeg"
                if file.lower().endswith(".png"): content_type = "image/png"
                elif file.lower().endswith(".webp"): content_type = "image/webp"
                elif file.lower().endswith(".svg"): content_type = "image/svg+xml"

                blob = bucket.blob(relative_path)
                blob.upload_from_filename(local_path, content_type=content_type)
                
                # blob.make_public()  # Disabled: Bucket uses Uniform Bucket-Level Access
                
                total_uploaded += 1
                if total_uploaded % 10 == 0:
                    print(f"Uploaded {total_uploaded} files...")
            except Exception as e:
                print(f"Failed to upload {relative_path}: {e}")

    print(f"\nMigration complete! Total files uploaded: {total_uploaded}")
    print("Now update your Vercel/Local .env with the GCS credentials.")

if __name__ == "__main__":
    upload_media_to_gcs()
