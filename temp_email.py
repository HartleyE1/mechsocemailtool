# temp_email.py
import os
import tempfile

# If the parent process set TEMP_EML_PATH, use it
env_path = os.environ.get("TEMP_EML_PATH")

if env_path:
    TEMP_EML_PATH = env_path
else:
    # Otherwise create a new one (only happens in the main GUI process)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        TEMP_EML_PATH = f.name