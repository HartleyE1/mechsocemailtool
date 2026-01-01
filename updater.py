import os
import sys
import json
import shutil
import tempfile
import platform
import requests

# Your GitHub Pages base URL
PAGES_BASE = "https://hartleye1.github.io/mechsocemailtool/download"

# Version file hosted on Pages
REMOTE_VERSION_URL = f"{PAGES_BASE}/version_info.json"

# Local version file bundled with the app
LOCAL_VERSION_FILE = "version_info.json"

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_local_version():
    with open(resource_path(LOCAL_VERSION_FILE), "r") as f:
        return json.load(f)["version"]


def get_remote_version():
    try:
        r = requests.get(REMOTE_VERSION_URL, timeout=5)
        return r.json()["version"]
    except Exception:
        print("Warning: Could not fetch remote version info.")
        return "0.0.0"


def is_outdated():
    return get_local_version() != get_remote_version()


def get_download_url():
    system = platform.system()

    if system == "Windows":
        return f"{PAGES_BASE}/windows/MechSoc Email Tool.exe"
    elif system == "Darwin":
        return f"{PAGES_BASE}/macos/mechsoc_email_tool_macos.zip"
    else:
        raise RuntimeError("Unsupported OS")


def download_update():
    url = get_download_url()
    print(f"Downloading update from {url}")

    r = requests.get(url, stream=True)
    r.raise_for_status()

    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    with open(temp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    return temp_path


def replace_app(downloaded_path):
    system = platform.system()

    if system == "Windows":
        current_exe = sys.argv[0]
        backup = current_exe + ".old"

        shutil.move(current_exe, backup)
        shutil.move(downloaded_path, current_exe)

    elif system == "Darwin":
        app_dir = os.path.abspath(os.path.join(sys.argv[0], "..", "..", ".."))
        backup = app_dir + ".old"

        temp_extract = tempfile.mkdtemp()
        shutil.unpack_archive(downloaded_path, temp_extract)

        new_app_path = os.path.join(temp_extract, "MechSocEmailTool.app")

        shutil.move(app_dir, backup)
        shutil.move(new_app_path, app_dir)

    else:
        raise RuntimeError("Unsupported OS")


def Update():
    print("Checking for updates...")

    if not is_outdated():
        print("Already up to date.")
        return

    print("Update available. Downloading...")
    downloaded = download_update()

    print("Replacing application...")
    replace_app(downloaded)

    print("Update complete. Restart the application.")