import gui
import pandas as pd
import email_generator
import tempfile
import os
import atexit
from temp_email import TEMP_EML_PATH
import multiprocessing

os.environ["TEMP_EML_PATH"] = TEMP_EML_PATH


def generate_emails(data: pd.DataFrame, output_folder, template_path):

    if (len(data) > 20):
        if not gui.large_dataset_warning():
            print("Not generating, user exited.")
            return

    # Convert CSV string to list of dictionaries
    data = data.to_dict(orient='records')

    # Generate emails using the email_generator module
    email_generator.generate_emails(template_path, data, output_folder)

    gui.finish_message()

def main():
    # Start the GUI
    gui.start_gui(generate_emails)
# Run the main function

@atexit.register
def cleanup_temp_files():
    try:
        os.remove(TEMP_EML_PATH)
    except OSError:
        pass

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

