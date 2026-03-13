import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
import os


def detect_landmarks(image_path):
    """
    Detects face and hand landmarks from an image.
    Returns: dict of coordinates for ears, neck, and wrist.
    """
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    mp_hands = mp.solutions.hands
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape
    
    results = {}
    
    # 1. Face Landmarks (Face Mesh)
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        res = face_mesh.process(img_rgb)
        if res.multi_face_landmarks:
            landmarks = res.multi_face_landmarks[0]
            # Landmark indices for try-on:
            # Left Ear: 234, Right Ear: 454
            # Neck/Chin area: 152 (chin bottom)
            results['left_ear']  = (int(landmarks.landmark[234].x * w), int(landmarks.landmark[234].y * h))
            results['right_ear'] = (int(landmarks.landmark[454].x * w), int(landmarks.landmark[454].y * h))
            results['chin']      = (int(landmarks.landmark[152].x * w), int(landmarks.landmark[152].y * h))
            
    # 2. Hand Landmarks
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2) as hands:
        res = hands.process(img_rgb)
        if res.multi_hand_landmarks:
            # For simplicity, take the first hand detected
            hand_landmarks = res.multi_hand_landmarks[0]
            # Wrist: 0
            results['wrist'] = (int(hand_landmarks.landmark[0].x * w), int(hand_landmarks.landmark[0].y * h))
            
    return results

def overlay_jewelry(base_image_path, overlay_image_path, position, scale=1.0, offset=(0,0)):
    """
    Overlays a jewelry PNG on the base image at a specific landmark.
    """
    base_img = Image.open(base_image_path).convert("RGBA")
    overlay  = Image.open(overlay_image_path).convert("RGBA")
    
    # Resize overlay based on scale
    nw = int(overlay.width * scale)
    nh = int(overlay.height * scale)
    overlay = overlay.resize((nw, nh), Image.LANCZOS)
    
    # Calculate position (center overlay on landmark + offset)
    px = position[0] - nw // 2 + offset[0]
    py = position[1] - nh // 2 + offset[1]
    
    base_img.paste(overlay, (px, py), overlay)
    return base_img.convert("RGB")

def process_tryon(user_image_path, jewelry_id, jewelry_type):
    """
    Automated process: detect -> select asset -> overlay -> save
    """
    landmarks = detect_landmarks(user_image_path)
    if not landmarks:
        return None
        
    # Logic to select correct landmark and scale based on type
    # This is a simplified version; real implementation needs fine-tuning per asset
    tryon_result = None
    
    # Placeholder asset path - in real app, fetch from JewelryCatalog
    asset_path = f"static/preference_app/tryon_assets/{jewelry_id}.png"
    if not os.path.exists(asset_path):
        # Fallback to a default if not found (for demo)
        asset_path = "static/preference_app/tryon_assets/default_necklace.png"

    if jewelry_type == "Necklace" and 'chin' in landmarks:
        tryon_result = overlay_jewelry(user_image_path, asset_path, landmarks['chin'], scale=1.5, offset=(0, 60))
    elif jewelry_type == "Earrings" and 'left_ear' in landmarks:
        # Overlay on both ears
        temp_img = overlay_jewelry(user_image_path, asset_path, landmarks['left_ear'], scale=0.3, offset=(0, 10))
        # Need to re-open for second paste or modify overlay_jewelry for multiple
        # For simplicity, just one ear in this v1
        tryon_result = temp_img
    elif jewelry_type == "Bangle" and 'wrist' in landmarks:
        tryon_result = overlay_jewelry(user_image_path, asset_path, landmarks['wrist'], scale=0.8)
        
    if tryon_result:
        output_filename = f"tryon_output_{jewelry_id}.jpg"
        output_path = os.path.join("media", "tryon", output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tryon_result.save(output_path, "JPEG")
        return output_path
        
    return None
