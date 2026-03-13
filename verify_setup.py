import fastapi
import uvicorn
import sklearn
import tensorflow as tf
import pandas as pd
import numpy as np
import nltk
import spacy
import transformers

print("FastAPI version:", fastapi.__version__)
print("TensorFlow version:", tf.__version__)
print("Pandas version:", pd.__version__)
print("NumPy version:", np.__version__)
print("Transformers version:", transformers.__version__)

try:
    nlp = spacy.load("en_core_web_sm")
    print("SpaCy model loaded successfully.")
except:
    print("SpaCy model 'en_core_web_sm' not found. Installing...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])

print("Environment verification complete.")
