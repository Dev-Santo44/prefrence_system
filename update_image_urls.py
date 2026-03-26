import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def update_urls():
    bucket_name = os.getenv("GS_BUCKET_NAME")
    if not bucket_name:
        print("Missing GS_BUCKET_NAME in .env")
        return

    base_url = f"https://storage.googleapis.com/{bucket_name}/"
    items = JewelryCatalog.objects.all()
    count = 0
    updated = 0
    
    print(f"Updating {items.count()} catalog items to use GCS CDN...")
    
    for item in items:
        # If the URL is a local /media/ path, rewrite it to GCS
        if item.image_url and item.image_url.startswith('/media/'):
            # Remove /media/ and prepend GCS base_url
            relative_path = item.image_url.replace('/media/', '', 1)
            # URL encode spaces to be safe
            relative_path = relative_path.replace(' ', '%20')
            item.image_url = base_url + relative_path
            item.save(update_fields=['image_url'])
            updated += 1
        count += 1
        
    print(f"Processed {count} items. Updated {updated} to use GCS CDN.")

if __name__ == "__main__":
    update_urls()
