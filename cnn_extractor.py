import os
import numpy as np
import requests
from io import BytesIO
import PIL
from PIL import Image

try:
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
    
    # Load model without top classification layer, pooling=avg to output a single 1280-d vector per image
    model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3), pooling='avg')
except ImportError:
    model = None
    print("Warning: TensorFlow not installed. Feature extraction will fail.")

def extract_features(image_path_or_url):
    """
    Given an image path or URL, returns a 1280-dimensional feature vector as a numpy array.
    """
    if model is None:
        raise RuntimeError("TensorFlow is not available. Cannot extract features.")
        
    try:
        if image_path_or_url.startswith('http'):
            import urllib.request
            import tempfile
            
            req = urllib.request.Request(
                image_path_or_url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req) as response:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(response.read())
                    tmp_path = tmp_file.name
                    
            img = Image.open(tmp_path)
            img.load() # Force load into memory
            os.remove(tmp_path)
        else:
            img = Image.open(image_path_or_url)
        
        img = img.convert('RGB')
        img = img.resize((224, 224))
        
        x = tf.keras.preprocessing.image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        features = model.predict(x, verbose=0)
        return features[0] # Return the 1D array of length 1280
    except Exception as e:
        print(f"Error extracting features for {image_path_or_url}: {e}")
        return None
