import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

# Curated Unsplash IDs for high-quality jewelry photography
UNSPLASH_MAP = {
    'Necklace': [
        '1599643478518-a784e5dc4c8f',
        '1611085583191-a3b1a3a2c4fe',
        '1515562141207-7a88fb7ce338',
        '1611937663712-1f488661858e'
    ],
    'Pendant': [
        '1599643478518-a784e5dc4c8f',
        '1611085583191-a3b1a3a2c4fe'
    ],
    'Earring': [
        '1635767798638-3e25273a8256',
        '1535632066927-ab7c9ab60908',
        '1598560942067-dc1365313a5b',
        '1629227831871-dc5322744a7b'
    ],
    'Ring': [
        '1605100804763-247f67b3557e',
        '1544273573-04022416b2a0',
        '1588444833075-45a4a5814571',
        '1603912627286-a96096144862'
    ],
    'Bracelet': [
        '1611591437281-460bfbe1220a',
        '1515562141207-7a88fb7ce338',
        '1617038260897-41a1f14a8ca0'
    ],
    'Bangle': [
        '1611591437281-460bfbe1220a',
        '1515562141207-7a88fb7ce338'
    ]
}

def fix_images():
    print("Correcting Jewelry Catalog images with Unsplash photography...")
    items = JewelryCatalog.objects.all()
    count = 0
    
    for item in items:
        # Get pool of IDs for the item type
        pool = UNSPLASH_MAP.get(item.item_type, [])
        if not pool:
            # Fallback for any unknown types
            photo_id = '1515562141207-7a88fb7ce338' 
        else:
            # Randomly pick from the pool to avoid duplicates
            photo_id = random.choice(pool)
            
        # Construct Unsplash URL with proper sizing
        new_url = f"https://images.unsplash.com/photo-{photo_id}?q=80&w=600&auto=format&fit=crop"
        
        item.image_url = new_url
        item.save(update_fields=['image_url'])
        count += 1
        
    print(f"Successfully updated image URLs for {count} jewelry items.")

if __name__ == "__main__":
    fix_images()
