import os
import django
import pandas as pd
import shutil
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def get_item_type(name, category):
    name = str(name).lower()
    category = str(category).lower()
    if any(k in name for k in ['neck', 'pendant', 'mangalsutra', 'chain']) or 'mangalsutra' in category:
        return 'Necklace'
    if any(k in name for k in ['earring', 'jhumka', 'stud']) or 'earring' in category:
        return 'Earrings'
    if any(k in name for k in ['ring', 'band', 'solitaire']) or 'solitaire' in category:
        return 'Ring'
    if any(k in name for k in ['bracelet', 'bangle', 'wrist']) or 'bangle' in category:
        return 'Bracelet'
    if 'nose' in name or 'nath' in name:
        return 'Nose Ring'
    if 'anklet' in name:
        return 'Anklet'
    return 'Other'

def get_material(name):
    name = str(name).lower()
    if 'diamond' in name: return 'Diamond'
    if 'gold' in name: return 'Gold'
    if 'silver' in name: return 'Silver'
    if 'platinum' in name: return 'Platinum'
    if 'rose gold' in name: return 'Rose Gold'
    return 'Gold'

def get_style(name):
    name = str(name).lower()
    if any(k in name for k in ['minimal', 'sleek', 'daily']): return 'Minimalist'
    if any(k in name for k in ['statement', 'heavy', 'grand']): return 'Statement'
    if any(k in name for k in ['modern', 'contemporary']): return 'Modern'
    if any(k in name for k in ['vintage', 'antique']): return 'Vintage'
    if any(k in name for k in ['boho', 'floral']): return 'Boho'
    return 'Modern'

def get_occasion(name, category):
    name = str(name).lower()
    category = str(category).lower()
    if any(k in name for k in ['bridal', 'wedding']): return 'Bridal'
    if any(k in name for k in ['party', 'celebration']): return 'Party'
    if any(k in name for k in ['work', 'office']): return 'Work'
    if any(k in name for k in ['daily', 'casual']): return 'Daily'
    if 'gift' in category: return 'Special-Occasion'
    return 'Casual'

def get_aesthetic(name):
    name = str(name).lower()
    if any(k in name for k in ['traditional', 'indian', 'ethnic', 'jhumka', 'mangalsutra']): return 'Traditional'
    return 'Western'

def parse_price(price_str):
    if pd.isna(price_str): return 0
    # Handle the rupee symbol and other non-numeric chars
    clean_str = "".join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))
    try:
        return int(float(clean_str))
    except:
        return 0

def update_catalog():
    excel_path = r"d:\web\client\pranali\new data\ecommerce.xlsx"
    images_dir = r"d:\web\client\pranali\new data\downloaded_images"
    media_target_dir = os.path.join(settings.MEDIA_ROOT, 'products', 'catalog')
    
    if not os.path.exists(media_target_dir):
        os.makedirs(media_target_dir, exist_ok=True)

    print("--- Clearing existing catalog ---")
    JewelryCatalog.objects.all().delete()

    print(f"--- Loading data from {excel_path} ---")
    df = pd.read_excel(excel_path)
    
    count_success = 0
    
    for i, row in df.iterrows():
        name = row.get('name', 'Unnamed Item')
        category = row.get('catagories', 'Other')
        prize_raw = row.get('prize', '0')
        img_src = row.get('image-src', '')
        
        price = parse_price(prize_raw)
        item_type = get_item_type(name, category)
        material = get_material(name)
        style = get_style(name)
        occasion = get_occasion(name, category)
        aesthetic = get_aesthetic(name)
        
        # Image handling
        img_filename = f"{i+1}.jpg"
        source_img_path = os.path.join(images_dir, img_filename)
        destination_img_path = os.path.join(media_target_dir, img_filename)
        
        final_img_url = ""
        if os.path.exists(source_img_path):
            shutil.copy(source_img_path, destination_img_path)
            final_img_url = f"/media/products/catalog/{img_filename}"
        else:
            # Fallback to external URL if local image missing
            final_img_url = img_src
            
        try:
            JewelryCatalog.objects.create(
                name=name,
                item_type=item_type,
                style=style,
                material=material,
                occasion=occasion,
                aesthetic=aesthetic,
                price=price,
                image_url=final_img_url,
                product_link="#"
            )
            count_success += 1
            if count_success % 10 == 0:
                print(f"Imported {count_success} items...")
        except Exception as e:
            print(f"Error importing row {i+1}: {e}")

    print(f"\nSUCCESSFULLY REPLACED CATALOG WITH {count_success} ITEMS!")

if __name__ == "__main__":
    update_catalog()
