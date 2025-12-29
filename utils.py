import pyperclip
import csv
import io
import pandas as pd

def paste_spreadsheet_data_to_csv():
    raw_text = pyperclip.paste()
    rows = [line.split('\t') for line in raw_text.strip().split('\n')]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue()

def csv_from_data_frame(df: pd.DataFrame) -> str:
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()