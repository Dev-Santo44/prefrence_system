import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def repopulate_catalog_local():
    """
    Clears the catalog and populates it with images found in media/products/
    """
    print("Clearing existing catalog...")
    JewelryCatalog.objects.all().delete()

    media_root = "d:/web/client/pranali/p_system/media"
    products_dir = os.path.join(media_root, "products")
    
    if not os.path.exists(products_dir):
        print(f"Error: {products_dir} does not exist.")
        return

    # Categories based on folder names
    categories = os.listdir(products_dir)
    total_added = 0

    # Probabilistic attributes for variety
    styles = ["Minimalist", "Statement", "Modern", "Classic", "Boho", "Vintage", "Traditional"]
    materials = ["Gold", "Silver", "Platinum", "Rose Gold", "Diamond", "Gemstone", "Artificial"]
    occasions = ["Daily Wear", "Party", "Bridal", "Formal", "Casual", "Work"]
    aesthetics = ["Western", "Traditional", "Ethnic", "Contemporary", "Fusion"]

    for cat in categories:
        cat_path = os.path.join(products_dir, cat)
        if not os.path.isdir(cat_path):
            continue
            
        print(f"Indexing category: {cat}...")
        itype = cat.capitalize()
        if cat == "nosering": itype = "Nose Ring"
        if cat == "earrings": itype = "Earrings"
        if cat == "pendant": itype = "Pendant"
        if cat == "anklet": itype = "Anklet"
        if cat == "bracelet": itype = "Bracelet"
        if cat == "ring": itype = "Ring"
        if cat == "necklace": itype = "Necklace"
        
        files = os.listdir(cat_path)
        for f in files:
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
                
            # Generate a readable name
            base_name = os.path.splitext(f)[0]
            # e.g. "necklace 1" -> "Luxe Necklace #1"
            parts = base_name.split()
            if len(parts) > 1 and parts[-1].isdigit():
                name = f"Premium {itype} #{parts[-1]}"
            else:
                name = f"Designer {itype} - {base_name.replace('_', ' ').title()}"

            # Pricing logic by category
            if cat == "ring": price = random.randint(2500, 95000)
            elif cat == "necklace": price = random.randint(8000, 250000)
            elif cat == "bangles": price = random.randint(5000, 80000)
            elif cat == "pendant": price = random.randint(3000, 45000)
            elif cat == "earrings": price = random.randint(1500, 35000)
            else: price = random.randint(2000, 50000)

            # Assign material based on common category traits (just for realism)
            mat = random.choice(materials)
            if "gold" in base_name.lower(): mat = "Gold"
            elif "silver" in base_name.lower(): mat = "Silver"
            elif "diamond" in base_name.lower(): mat = "Diamond"

            img_url = f"/media/products/{cat}/{f}"
            
            JewelryCatalog.objects.create(
                name=name,
                item_type=itype,
                style=random.choice(styles),
                material=mat,
                occasion=random.choice(occasions),
                aesthetic=random.choice(aesthetics),
                price=price,
                image_url=img_url,
                product_link="#"
            )
            total_added += 1
            
    print(f"\nSuccessfully populated database with {total_added} products.")
    print("Each item is linked to your local 'scrapped' dataset.")

if __name__ == "__main__":
    repopulate_catalog_local()
