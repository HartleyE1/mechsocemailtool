# temp_email.py
import tempfile
import os

# Create a persistent temp file for the entire runtime
with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
    TEMP_EML_PATH = f.name