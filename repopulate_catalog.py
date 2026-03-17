import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import JewelryCatalog

def repopulate_catalog():
    # Clear old catalog
    JewelryCatalog.objects.all().delete()

    # New jewelry data - 30 items
    jewelry_items = [
        # Rings
        ("Classic Gold Solitaire Ring", "Ring", "Minimalist", "Gold", "Bridal", "Traditional", 45000, "https://images.unsplash.com/photo-1605100804763-247f67b3557e?q=80&w=600&auto=format"),
        ("Modern Geometric Silver Ring", "Ring", "Modern", "Silver", "Casual", "Western", 3500, "https://images.unsplash.com/photo-1544441893-675973e31985?q=80&w=600&auto=format"),
        ("Rose Gold Leaf Band", "Ring", "Boho", "Rose Gold", "Daily", "Western", 8200, "https://images.unsplash.com/photo-1598560912170-659f1396f4be?q=80&w=600&auto=format"),
        ("Midnight Onyx Statement Ring", "Ring", "Statement", "Black Metal", "Party", "Gothic", 12500, "https://images.unsplash.com/photo-1603561591411-071c4f74391a?q=80&w=600&auto=format"),
        ("Vintage Sapphire Ring", "Ring", "Vintage", "Platinum", "Special", "Traditional", 120000, "https://images.unsplash.com/photo-1573408301185-9146fe634ad0?q=80&w=600&auto=format"),
        
        # Necklaces
        ("Dainty Diamond Pendant", "Necklace", "Minimalist", "Gold", "Daily", "Western", 28000, "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=600&auto=format"),
        ("Chunky Silver Choker", "Necklace", "Statement", "Silver", "Party", "Western", 5500, "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?q=80&w=600&auto=format"),
        ("Emerald Harmony Necklace", "Necklace", "Elegant", "White Gold", "Bridal", "Traditional", 85000, "https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?q=80&w=600&auto=format"),
        ("Boho Turqoise Bead Chain", "Necklace", "Boho", "Mixed", "Casual", "Western", 2200, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=600&auto=format"),
        ("Royal Pearl String", "Necklace", "Vintage", "Pearl", "Formal", "Traditional", 35000, "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?q=80&w=600&auto=format"),
        
        # Earrings
        ("Sleek Silver Hoops", "Earrings", "Minimalist", "Silver", "Daily", "Western", 1500, "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?q=80&w=600&auto=format"),
        ("Floral Enamel Jhumkas", "Earrings", "Traditional", "Gold Plated", "Party", "Traditional", 4800, "https://images.unsplash.com/photo-1630019058353-5ff3f404f2f4?q=80&w=600&auto=format"),
        ("Art Deco Crystal Drops", "Earrings", "Statement", "Crystal", "Special", "Western", 9500, "https://images.unsplash.com/photo-1589128777073-263566ae5e4d?q=80&w=600&auto=format"),
        ("Cubic Zirconia Studs", "Earrings", "Modern", "Sterling Silver", "Daily", "Western", 2500, "https://images.unsplash.com/photo-1588891825651-70ba4355554f?q=80&w=600&auto=format"),
        ("Tassel Boho Earrings", "Earrings", "Boho", "Fabric/Beads", "Casual", "Western", 1200, "https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?q=80&w=600&auto=format"),
        
        # Bracelets
        ("Tennis Diamond Bracelet", "Bracelet", "Luxury", "White Gold", "Special", "Western", 150000, "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=600&auto=format"),
        ("Handcrafted Leather Cuff", "Bracelet", "Gothic", "Leather", "Casual", "Western", 3200, "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=600&auto=format"),
        ("Gold Charm Bracelet", "Bracelet", "Minimalist", "Gold", "Daily", "Western", 22000, "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=600&auto=format"),
        ("Traditional Kemp Bangle", "Bracelet", "Traditional", "Gold Plated", "Bridal", "Traditional", 12500, "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=600&auto=format"),
        ("Minimalist Silver Cuff", "Bracelet", "Modern", "Silver", "Work", "Western", 4500, "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=600&auto=format"),
    ]

    for name, itype, style, material, occasion, aesthetic, price, img in jewelry_items:
        JewelryCatalog.objects.create(
            name=name,
            item_type=itype,
            style=style,
            material=material,
            occasion=occasion,
            aesthetic=aesthetic,
            price=price,
            image_url=img,
            product_link="#"
        )

    print(f"Successfully repopulated catalog with {len(jewelry_items)} items.")

if __name__ == "__main__":
    repopulate_catalog()
