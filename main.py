import gui
import pandas as pd
import email_generator
from io import StringIO
import utils


def generate_emails(data: pd.DataFrame, output_folder, template_path):
    # Convert CSV string to list of dictionaries
    data = data.to_dict(orient='records')

    # Generate emails using the email_generator module
    email_generator.generate_emails(template_path, data, output_folder)

    gui.finish_message()

def __main__():
    # Start the GUI
    gui.start_gui(generate_emails)

# Run the main function

if __name__ == "__main__":
    __main__()