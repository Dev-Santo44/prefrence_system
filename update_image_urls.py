import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def update_urls():
    items = JewelryCatalog.objects.all()
    count = 0
    for item in items:
        # Use Picsum seeds to get distinct static images that download reliably
        item.image_url = f"https://picsum.photos/seed/{item.id}/500/500"
        item.save(update_fields=['image_url'])
        count += 1
        
    print(f"Updated {count} items with reliable image URLs.")

if __name__ == "__main__":
    update_urls()
