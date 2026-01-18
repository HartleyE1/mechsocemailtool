import os, sys, time, shutil, platform, tempfile

downloaded = sys.argv[1]
target = sys.argv[2]

# Wait for the main app to fully exit
time.sleep(1)

# Perform the replacement
system = platform.system()

if system == "Windows":
    backup = target + ".old"
    shutil.move(target, backup)
    shutil.move(downloaded, target)

elif system == "Darwin":
    app_dir = os.path.abspath(os.path.join(target, "..", "..", ".."))
    backup = app_dir + ".old"

    temp_extract = tempfile.mkdtemp()
    shutil.unpack_archive(downloaded, temp_extract)

    new_app_path = os.path.join(temp_extract, "MechSocEmailTool.app")

    shutil.move(app_dir, backup)
    shutil.move(new_app_path, app_dir)

os.remove(downloaded)

if (__name__ == "__main__"):
    os.remove(__file__)