import os
import random
import django
import sys

# Setup Django path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

# Map DB categories to local folders
CATEGORY_MAP = {
    'Earring': 'earrings',
    'Necklace': 'necklace',
    'Ring': 'ring',
    'Pendant': 'pendant',
    'Bracelet': 'bracelet'
}

SOURCE_PATH = os.path.join(BASE_DIR, 'media', 'products')

def update_product_images():
    products = JewelryCatalog.objects.all()
    print(f"Total products in DB: {products.count()}")
    
    # Pre-load image lists
    image_pools = {}
    for db_cat, folder_name in CATEGORY_MAP.items():
        folder_path = os.path.join(SOURCE_PATH, folder_name)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            image_pools[db_cat] = files
            print(f"Pool for {db_cat}: {len(files)} images")
        else:
            print(f"Warning: Folder not found: {folder_path}")
    
    # Other images for fallback
    other_folders = ['anklet', 'nosering']
    all_other_images = []
    for f in other_folders:
        path = os.path.join(SOURCE_PATH, f)
        if os.path.exists(path):
            all_other_images.extend([os.path.join(f, img) for img in os.listdir(path) if img.lower().endswith(('.jpg', '.jpeg', '.png'))])

    updated_count = 0
    # Shuffle pools for variety
    for cat in image_pools:
        random.shuffle(image_pools[cat])

    for i, product in enumerate(products):
        pool = image_pools.get(product.item_type)
        if pool and len(pool) > 0:
            img_file = pool[i % len(pool)]
            folder = CATEGORY_MAP[product.item_type]
            # Use /media/ URL
            product.image_url = f"/media/products/{folder}/{img_file}"
            product.save()
            updated_count += 1
        elif all_other_images:
            img_rel_path = random.choice(all_other_images)
            product.image_url = f"/media/products/{img_rel_path.replace('\\', '/')}"
            product.save()
            updated_count += 1
            
    print(f"Successfully updated {updated_count} products with unique images.")

if __name__ == "__main__":
    update_product_images()
