from PIL import Image
import numpy as np
import os

def _remove_background(pil_img):
    img_rgba = pil_img.convert("RGBA")
    data = np.array(img_rgba)
    red, green, blue, alpha = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    white_mask = (red > 230) & (green > 230) & (blue > 230)
    data[:,:,3][white_mask] = 0
    return Image.fromarray(data)

asset_path = r'd:\web\client\pranali\p_system\static\preference_app\tryon_assets\nacklace_5.png'
if os.path.exists(asset_path):
    img = Image.open(asset_path).convert("RGBA")
    original_pixel = img.getpixel((0,0))
    print(f"Original (0,0) pixel: {original_pixel}")
    
    clean_img = _remove_background(img)
    new_pixel = clean_img.getpixel((0,0))
    print(f"Modified (0,0) pixel: {new_pixel}")
    
    if new_pixel[3] == 0:
        print("SUCCESS: Background pixel is now transparent.")
    else:
        print("FAILURE: Background pixel is still opaque.")
else:
    print(f"Asset not found: {asset_path}")
