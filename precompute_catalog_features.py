import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog
from cnn_extractor import extract_features

def precompute_features():
    items = JewelryCatalog.objects.filter(visual_features__isnull=True)
    total = items.count()
    print(f"Items requiring feature extraction: {total}")
    
    start_time = time.time()
    processed = 0
    
    for item in items:
        if not item.image_url:
            continue
            
        features = extract_features(item.image_url)
        if features is not None:
            # Store as list in JSONField
            item.visual_features = features.tolist()
            item.save(update_fields=['visual_features'])
            processed += 1
            
        if processed % 10 == 0:
            print(f"Processed {processed}/{total} items...")
            
    end_time = time.time()
    print(f"Successfully processed {processed} items in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    precompute_features()
