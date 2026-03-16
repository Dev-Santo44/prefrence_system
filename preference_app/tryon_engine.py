import cv2
import numpy as np
from PIL import Image
import os
import random
import urllib.request

from django.conf import settings

# ── MediaPipe — safe import with version detection ────────────────────────────
MEDIAPIPE_AVAILABLE   = False
NEW_API               = False
mp                    = None
mp_python             = None
FaceLandmarker        = None
FaceLandmarkerOptions = None
HandLandmarker        = None
HandLandmarkerOptions = None

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    MEDIAPIPE_VERSION   = tuple(int(x) for x in mp.__version__.split(".")[:2])
    NEW_API             = MEDIAPIPE_VERSION >= (0, 10)

    if NEW_API:
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
            HandLandmarker,
            HandLandmarkerOptions,
        )
    else:
        # Verify old solutions API exists
        _ = mp.solutions.face_mesh
        _ = mp.solutions.hands

    print(f"[TryOn] MediaPipe {mp.__version__} loaded  |  NEW_API={NEW_API}")

except ImportError as e:
    print(f"[TryOn] WARNING: MediaPipe not installed — {e}")
except Exception as e:
    print(f"[TryOn] WARNING: MediaPipe import issue — {e}")


# ── Asset resolver ────────────────────────────────────────────────────────────

def _get_asset_path(jewelry_id, jewelry_type):
    """
    Resolves the correct PNG asset based on jewelry type.
    Priority: exact {jewelry_id}.png  →  type-matched file  →  any PNG
    """
    assets_dir = os.path.join(
        settings.BASE_DIR, 'static', 'preference_app', 'tryon_assets'
    )

    if not os.path.exists(assets_dir):
        return None

    # 1. Exact match by jewelry_id
    exact = os.path.join(assets_dir, f"{jewelry_id}.png")
    if os.path.exists(exact):
        return exact

    # 2. Type-based prefix matching
    # Handles "nacklace" typo in your existing filenames
    type_prefixes = {
        "Earrings": ["earring_"],
        "Necklace": ["necklace_", "nacklace_"],
        "Bangle":   ["bangle_", "ring_"],
        "Ring":     ["ring_"],
        "Set":      ["necklace_with_earring"],
    }

    prefixes = type_prefixes.get(jewelry_type, [])
    matches  = []

    for f in os.listdir(assets_dir):
        if not f.endswith('.png'):
            continue
        if jewelry_type != "Set" and "with_earring" in f:
            continue
        for prefix in prefixes:
            if f.startswith(prefix):
                matches.append(os.path.join(assets_dir, f))
                break

    if matches:
        return random.choice(matches)

    # 3. Final fallback — any PNG
    all_pngs = [
        os.path.join(assets_dir, f)
        for f in os.listdir(assets_dir)
        if f.endswith('.png') and 'with_earring' not in f
    ]
    return random.choice(all_pngs) if all_pngs else None


# ── Model downloader (for NEW_API only) ───────────────────────────────────────

def _ensure_models():
    """Downloads MediaPipe .task model files if not already present."""
    models_dir = os.path.join(settings.BASE_DIR, 'models', 'mediapipe')
    os.makedirs(models_dir, exist_ok=True)

    files = {
        'face_landmarker.task': (
            "https://storage.googleapis.com/mediapipe-models/"
            "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        ),
        'hand_landmarker.task': (
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        ),
    }

    paths = {}
    for filename, url in files.items():
        dest = os.path.join(models_dir, filename)
        if not os.path.exists(dest):
            print(f"[TryOn] Downloading {filename} ...")
            urllib.request.urlretrieve(url, dest)
            print(f"[TryOn] Saved → {dest}")
        paths[filename] = dest

    return paths['face_landmarker.task'], paths['hand_landmarker.task']


# ── Landmark detector ─────────────────────────────────────────────────────────

def _detect_landmarks(image_path):
    if not MEDIAPIPE_AVAILABLE:
        raise RuntimeError("MediaPipe not installed. Run: pip install mediapipe")

    print(f"[TryOn] _detect_landmarks called with: {image_path}")
    print(f"[TryOn] File exists: {os.path.exists(image_path)}")

    img = cv2.imread(image_path)
    if img is None:
        print("[TryOn] ❌ cv2.imread returned None — file unreadable")
        return None

    print(f"[TryOn] ✅ Image loaded — shape: {img.shape}")
    
    img_rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _   = img.shape
    landmarks = {}

    if NEW_API:
        print("[TryOn] Using NEW_API (Tasks API)")
        face_model_path, hand_model_path = _ensure_models()
        print(f"[TryOn] Face model: {os.path.exists(face_model_path)}")
        print(f"[TryOn] Hand model: {os.path.exists(hand_model_path)}")

        face_opts = FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=face_model_path),
            num_faces=1,
        )
        with FaceLandmarker.create_from_options(face_opts) as detector:
            mp_img      = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            face_result = detector.detect(mp_img)
            print(f"[TryOn] Face landmarks found: {len(face_result.face_landmarks) if face_result.face_landmarks else 0}")

            if face_result.face_landmarks:
                lm = face_result.face_landmarks[0]
                landmarks['left_ear']  = (int(lm[234].x * w), int(lm[234].y * h))
                landmarks['right_ear'] = (int(lm[454].x * w), int(lm[454].y * h))
                landmarks['chin']      = (int(lm[152].x * w), int(lm[152].y * h))
                mid_x = (landmarks['left_ear'][0] + landmarks['right_ear'][0]) // 2
                landmarks['neck']         = (mid_x, landmarks['chin'][1] + int(h * 0.10))
                landmarks['ear_distance'] = abs(landmarks['right_ear'][0] - landmarks['left_ear'][0])
                print(f"[TryOn] ✅ Ears: L={landmarks['left_ear']}  R={landmarks['right_ear']}")
                
        hand_opts = HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=hand_model_path),
            num_hands=1,
        )
        with HandLandmarker.create_from_options(hand_opts) as hand_detector:
            mp_img      = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            hand_result = hand_detector.detect(mp_img)
            print(f"[TryOn] Hand landmarks found: {len(hand_result.hand_landmarks) if hand_result.hand_landmarks else 0}")
            
            if hand_result.hand_landmarks:
                lm = hand_result.hand_landmarks[0]
                landmarks['wrist'] = (int(lm[0].x * w), int(lm[0].y * h))
                print(f"[TryOn] ✅ Wrist: {landmarks['wrist']}")

    else:
        print("[TryOn] Using OLD_API (solutions API)")
        with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
            results = face_mesh.process(img_rgb)
            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark
                landmarks['left_ear']  = (int(lm[234].x * w), int(lm[234].y * h))
                landmarks['right_ear'] = (int(lm[454].x * w), int(lm[454].y * h))
                landmarks['chin']      = (int(lm[152].x * w), int(lm[152].y * h))
                mid_x = (landmarks['left_ear'][0] + landmarks['right_ear'][0]) // 2
                landmarks['neck']         = (mid_x, landmarks['chin'][1] + int(h * 0.10))
                landmarks['ear_distance'] = abs(landmarks['right_ear'][0] - landmarks['left_ear'][0])
                print(f"[TryOn] ✅ OLD_API Ears: L={landmarks['left_ear']}  R={landmarks['right_ear']}")
                
        with mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
            results = hands.process(img_rgb)
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark
                landmarks['wrist'] = (int(lm[0].x * w), int(lm[0].y * h))
                print(f"[TryOn] ✅ OLD_API Wrist: {landmarks['wrist']}")

    print(f"[TryOn] Final landmarks keys: {list(landmarks.keys())}")
    return landmarks if landmarks else None


def _remove_background(pil_img):
    """
    Dynamically removes near-white background from a PIL image.
    Converts to RGBA and sets white-ish pixels to (0,0,0,0).
    """
    img_rgba = pil_img.convert("RGBA")
    data = np.array(img_rgba)

    # Define white-ish range (R,G,B > 230)
    # Most jewelry assets have white (255,255,255) or light gray backgrounds
    red, green, blue, alpha = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    white_mask = (red > 230) & (green > 230) & (blue > 230)

    # Set alpha to 0 for white pixels
    data[:,:,3][white_mask] = 0

    return Image.fromarray(data)

# ── PNG overlay helper ────────────────────────────────────────────────────────

def _overlay_png(base_img_pil, overlay_path, center_x, center_y, width, height):
    """
    Pastes a PNG overlay centered at (center_x, center_y),
    resized to (width × height).  base_img_pil must be RGBA.
    """
    width  = max(1, width)
    height = max(1, height)

    overlay = Image.open(overlay_path).convert("RGBA")

    # Dynamic background removal check
    # If top-left pixel is white-ish, we assume it's a solid background that needs removal
    first_pixel = overlay.getpixel((0, 0))
    if first_pixel[0] > 230 and first_pixel[1] > 230 and first_pixel[2] > 230:
        overlay = _remove_background(overlay)

    overlay = overlay.resize((width, height), Image.LANCZOS)

    paste_x = center_x - width  // 2
    paste_y = center_y - height // 2

    # Clamp so overlay never goes outside image bounds
    paste_x = max(0, min(paste_x, base_img_pil.width  - width))
    paste_y = max(0, min(paste_y, base_img_pil.height - height))

    base_img_pil.paste(overlay, (paste_x, paste_y), overlay)
    return base_img_pil


# ── Main pipeline ─────────────────────────────────────────────────────────────

def process_tryon(user_image_path, jewelry_id, jewelry_type):
    """
    Full try-on pipeline:
      1. Detect face / hand landmarks
      2. Resolve correct PNG asset
      3. Overlay jewelry at the correct position and scale
      4. Save result to media/tryon/ and return the path

    Returns output_path (str) on success, None on failure.
    """

    # Step 1 — Landmarks
    landmarks = _detect_landmarks(user_image_path)
    if not landmarks:
        print(f"[TryOn] No landmarks detected in: {user_image_path}")
        return None

    # Step 2 — Asset
    asset_path = _get_asset_path(jewelry_id, jewelry_type)
    if not asset_path:
        print(f"[TryOn] No PNG asset found for type: {jewelry_type}")
        return None

    print(f"[TryOn] Using asset: {os.path.basename(asset_path)}")

    # Step 3 — Open base image
    base      = Image.open(user_image_path).convert("RGBA")
    img_w, img_h = base.size
    ear_dist  = landmarks.get('ear_distance', img_w // 4)

    # Step 4 — Overlay by type
    if jewelry_type == "Earrings":
        if 'left_ear' not in landmarks or 'right_ear' not in landmarks:
            print("[TryOn] Ear landmarks not found")
            return None

        earring_size = max(30, int(ear_dist * 0.22))

        # Left earring
        base = _overlay_png(
            base, asset_path,
            center_x = landmarks['left_ear'][0],
            center_y  = landmarks['left_ear'][1] + earring_size // 2,
            width     = earring_size,
            height    = int(earring_size * 1.4),   # earrings are taller than wide
        )

        # Right earring — horizontally mirrored
        mirrored     = Image.open(asset_path).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
        tmp_path     = asset_path.replace('.png', '_mirror_tmp.png')
        mirrored.save(tmp_path)

        base = _overlay_png(
            base, tmp_path,
            center_x = landmarks['right_ear'][0],
            center_y  = landmarks['right_ear'][1] + earring_size // 2,
            width     = earring_size,
            height    = int(earring_size * 1.4),
        )

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    elif jewelry_type == "Necklace":
        if 'neck' not in landmarks:
            print("[TryOn] Neck landmark not found")
            return None

        necklace_w = max(80, int(ear_dist * 1.1))
        necklace_h = max(40, int(necklace_w * 0.5))

        base = _overlay_png(
            base, asset_path,
            center_x = landmarks['neck'][0],
            center_y  = landmarks['neck'][1],
            width     = necklace_w,
            height    = necklace_h,
        )

    elif jewelry_type in ("Ring", "Bangle"):
        if 'wrist' not in landmarks:
            print("[TryOn] Wrist landmark not found — hand may not be visible")
            return None

        bangle_size = max(40, int(img_w * 0.12))

        base = _overlay_png(
            base, asset_path,
            center_x = landmarks['wrist'][0],
            center_y  = landmarks['wrist'][1],
            width     = bangle_size,
            height    = bangle_size,
        )

    elif jewelry_type == "Set":
        # Combo: necklace + earrings from one asset
        if 'neck' in landmarks:
            necklace_w = max(80, int(ear_dist * 1.1))
            base = _overlay_png(
                base, asset_path,
                center_x = landmarks['neck'][0],
                center_y  = landmarks['neck'][1],
                width     = necklace_w,
                height    = int(necklace_w * 0.8),
            )
    else:
        print(f"[TryOn] Unknown jewelry_type: {jewelry_type}")
        return None

    # Step 5 — Save output
    output_dir = os.path.join(settings.MEDIA_ROOT, 'tryon')
    os.makedirs(output_dir, exist_ok=True)

    safe_basename    = os.path.basename(user_image_path).replace(' ', '_')
    output_filename  = f"tryon_{jewelry_id}_{safe_basename}"
    if not output_filename.endswith('.jpg'):
        output_filename = output_filename.rsplit('.', 1)[0] + '.jpg'

    output_path = os.path.join(output_dir, output_filename)
    base.convert("RGB").save(output_path, "JPEG", quality=92)

    print(f"[TryOn] Result saved → {output_path}")
    return output_path