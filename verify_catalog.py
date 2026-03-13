import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

total = JewelryCatalog.objects.count()
print(f"Total Items: {total}")

if total > 0:
    print("\nSample Item 1:")
    item1 = JewelryCatalog.objects.first()
    print(f"Name: {item1.name}")
    print(f"Type: {item1.item_type}")
    print(f"Style: {item1.style}")
    print(f"Material: {item1.material}")
    print(f"Occasion: {item1.occasion}")
    print(f"Price: ₹{item1.price}")
    print(f"Price Range: {item1.price_range}")
    print(f"Image_url: {item1.image_url}")

    print("\nPrice Range Distribution:")
    print(f"Economy (< 5000): {JewelryCatalog.objects.filter(price_range='Economy').count()}")
    print(f"Mid-range (5000-20000): {JewelryCatalog.objects.filter(price_range='Mid-range').count()}")
    print(f"Luxury (> 20000): {JewelryCatalog.objects.filter(price_range='Luxury').count()}")
