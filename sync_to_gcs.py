import os
import json
import django
from google.cloud import storage
from dotenv import load_dotenv

# Setup Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

load_dotenv()

GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
GS_CREDENTIALS_JSON = os.getenv("GS_CREDENTIALS_JSON")

def sync_to_gcs():
    if not GS_BUCKET_NAME or not GS_CREDENTIALS_JSON:
        print("Missing GCS credentials in .env")
        return

    # Setup GCS Client
    cred_dict = json.loads(GS_CREDENTIALS_JSON.strip("'"))
    client = storage.Client.from_service_account_info(cred_dict)
    bucket = client.bucket(GS_BUCKET_NAME)

    local_media_dir = r"d:\web\client\pranali\p_system\media\products\catalog"
    gcs_base_path = "products/catalog/"

    if not os.path.exists(local_media_dir):
        print(f"Local directory not found: {local_media_dir}")
        return

    # 1. Upload images
    print(f"--- Uploading images to GCS bucket: {GS_BUCKET_NAME} ---")
    files = [f for f in os.listdir(local_media_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    upload_count = 0
    for filename in files:
        local_path = os.path.join(local_media_dir, filename)
        remote_path = f"{gcs_base_path}{filename}"
        
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        
        upload_count += 1
        if upload_count % 10 == 0:
            print(f"Uploaded {upload_count} images...")

    print(f"Successfully uploaded {upload_count} images to GCS.")

    # 2. Update Database
    print("\n--- Updating database URLs ---")
    base_gcs_url = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
    
    updated_items = 0
    # Find items that have local paths starting with /media/products/catalog/
    catalog_items = JewelryCatalog.objects.filter(image_url__startswith='/media/products/catalog/')
    
    for item in catalog_items:
        filename = os.path.basename(item.image_url)
        new_url = f"{base_gcs_url}{gcs_base_path}{filename}"
        item.image_url = new_url
        item.save()
        updated_items += 1

    print(f"Successfully updated {updated_items} records in DB.")
    print("\n✅ SYNC COMPLETE! Images should now be visible on the website.")

if __name__ == "__main__":
    sync_to_gcs()
