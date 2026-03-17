import os
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def import_from_sql():
    sql_file = r"C:\Users\ASUS\OneDrive\Desktop\ss\jewellery_full_and_final_dataset.sql"
    
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    print("Clearing existing catalog...")
    JewelryCatalog.objects.all().delete()

    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all INSERT INTO values
    # Pattern: ('val1', 'val2', ..., 'val8')
    pattern = re.compile(r"\((?P<vals>'.*?')\)", re.DOTALL)
    
    # Actually, SQL values are separated by commas, and can contain escaped characters.
    # Simple regex might be risky. Let's find the values after 'VALUES'
    values_start = content.find("VALUES")
    if values_start == -1:
        print("Error: VALUES not found in SQL.")
        return
    
    raw_values = content[values_start + 6:]
    # Clean up tailing COMMIT etc.
    raw_values = raw_values.split(";")[0]
    
    # Split by '), ('
    rows = raw_values.split("),")
    
    total_added = 0
    
    # For path checking
    media_root = "d:/web/client/pranali/p_system/media"

    for row in rows:
        row = row.strip().strip("() ")
        # Split by ', ' but be careful with values containing commas
        # Since these values are properly quoted, we can use a more robust split
        from shlex import split
        # shlex works well for quoted strings, but we need to handle the SQL escaping...
        # Let's use a simpler approach for this specific file since I saw the data.
        # Values are like '1', 'Royal Shine Drops', ...
        items = []
        current = ""
        in_quote = False
        for char in row:
            if char == "'" and (not current or current[-1] != "\\"):
                in_quote = not in_quote
            elif char == "," and not in_quote:
                items.append(current.strip().strip("'"))
                current = ""
            else:
                current += char
        items.append(current.strip().strip("'"))

        if not items or items[0] == "ID":
            continue

        if len(items) < 8:
            continue

        id_val, name, itype, category, path, desc, tags, price = items[:8]
        
        # Mapping mapping
        # path is like /assets/products/earrings/earring 1.jpg
        # we need /media/products/earrings/earring 1.jpg
        img_url = path.replace("/assets/", "/media/")
        
        # Verify image existence (try original, then try jpeg/jpg swap)
        full_img_path = os.path.join(media_root, img_url.replace("/media/", ""))
        if not os.path.exists(full_img_path):
            # Try switching extension
            if full_img_path.endswith(".jpg"):
                alt = full_img_path.replace(".jpg", ".jpeg")
            elif full_img_path.endswith(".jpeg"):
                alt = full_img_path.replace(".jpeg", ".jpg")
            else:
                alt = full_img_path
                
            if os.path.exists(alt):
                img_url = img_url.replace(".jpg", ".jpeg") if ".jpg" in img_url else img_url.replace(".jpeg", ".jpg")
            else:
                print(f"Warning: Image not found: {full_img_path}")

        # Map style/aesthetic from tags or category
        style = "Modern"
        occasion = "Casual"
        aesthetic = "Western"
        
        lower_tags = tags.lower()
        if "traditional" in lower_tags or "ethnic" in lower_tags: aesthetic = "Traditional"
        if "bridal" in lower_tags or "wedding" in lower_tags: occasion = "Bridal"
        if "minimal" in lower_tags: style = "Minimalist"
        if "party" in lower_tags: occasion = "Party"
        if "daily" in lower_tags: occasion = "Daily Wear"
        if "statement" in lower_tags: style = "Statement"
        
        # Clean price
        try:
            price_int = int(re.sub(r"[^\d]", "", price))
        except:
            price_int = 0

        JewelryCatalog.objects.create(
            name=name,
            item_type=itype,
            style=style,
            material=category,
            occasion=occasion,
            aesthetic=aesthetic,
            price=price_int,
            image_url=img_url,
            product_link="#"
        )
        total_added += 1

    print(f"Successfully imported {total_added} products from SQL.")

if __name__ == "__main__":
    import_from_sql()
