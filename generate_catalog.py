import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

# Dummy Data Pools
ADJECTIVES = ["Radiant", "Eternity", "Celestial", "Royal", "Enchanted", "Vintage", "Modern", "Classic", "Graceful", "Regal", "Luminous", "Majestic", "Opulent", "Delicate", "Bold", "Sparkling"]
NOUNS = ["Halo", "Solitaire", "Cluster", "Band", "Choker", "Pendant", "Drops", "Hoops", "Studs", "Bracelet", "Bangle", "Mangalsutra", "Chain", "Princess", "Queen", "Tear"]
MATERIALS = ["Gold", "Silver", "Platinum", "Rose Gold", "White Gold", "Diamond", "Pearl", "Sapphire", "Ruby", "Emerald", "American Diamond"]
STYLES = ["Minimalist", "Statement", "Classic", "Modern", "Vintage", "Geometric", "Delicate", "Bold"]
OCCASIONS = ["Everyday", "Bridal", "Party", "Work", "Formal", "Casual", "Evening", "Gift"]
AESTHETICS = ["Traditional", "Western", "Boho", "Modern", "Art Deco", "Floral", "Sleek", "Edgy"]
ITEM_TYPES = ["Ring", "Necklace", "Earring", "Bracelet", "Bangle", "Pendant"]

# Placeholder realistic jewelry images from unsplash source
IMAGES = [
    "https://images.unsplash.com/photo-1599643477874-ce4ad5b3bb3c?w=500&q=80",
    "https://images.unsplash.com/photo-1622398925373-3f91b1e275f5?w=500&q=80",
    "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=500&q=80",
    "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=500&q=80",
    "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?w=500&q=80",
    "https://images.unsplash.com/photo-1602751584552-8ba7a6f23b2d?w=500&q=80",
    "https://images.unsplash.com/photo-1596944924616-7b38e7cfac36?w=500&q=80",
    "https://images.unsplash.com/photo-1617264627914-f5f4bedbc94a?w=500&q=80",
    "https://images.unsplash.com/photo-1599643478514-4a5fdc813583?w=500&q=80",
    "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=500&q=80"
]

def generate_catalog(count=220):
    print(f"Generating {count} jewelry items...")
    
    # Clear existing to avoid duplicates if re-run
    JewelryCatalog.objects.all().delete()
    
    items_created = 0
    for _ in range(count):
        item_type = random.choice(ITEM_TYPES)
        material = random.choice(MATERIALS)
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        
        name = f"{adj} {material} {noun} {item_type}"
        style = random.choice(STYLES)
        occasion = random.choice(OCCASIONS)
        aesthetic = random.choice(AESTHETICS)
        
        # Realistic pricing
        if material in ["Platinum", "Diamond", "Sapphire", "Ruby", "Emerald"]:
            price = random.randint(25000, 150000)
        elif material in ["Gold", "White Gold", "Rose Gold"]:
            price = random.randint(10000, 80000)
        else:
            price = random.randint(1500, 12000)
            
        # Price is rounded to hundreds for realism
        price = (price // 100) * 100
        
        image_url = random.choice(IMAGES)
        
        JewelryCatalog.objects.create(
            name=name,
            item_type=item_type,
            style=style,
            material=material,
            occasion=occasion,
            aesthetic=aesthetic,
            price=price,
            image_url=image_url,
            product_link="#"
        )
        items_created += 1
        
        if items_created % 50 == 0:
            print(f"Created {items_created} items...")

    print(f"Success! Total items in DB: {JewelryCatalog.objects.count()}")

if __name__ == "__main__":
    generate_catalog()
