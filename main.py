from nicegui import ui
import argparse
import csv
import io
import json
from pathlib import Path
import re
import pandas as pd
import pyperclip
import email_builder
from tkinter import filedialog

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def main():
    
    argument_parser = argparse.ArgumentParser(description="MechSoc Email Tool")
    argument_parser.add_argument("--test", action="store_true", help="Start the UI in test mode (runs in non-native mode for easier debugging)")
    args = argument_parser.parse_args()

    global df
    df = initialise_dataframe()

    UI_start(test=args.test)


# ---- Graphical User Interface ----

def UI_start(test=False):
    favicon_path = str(ASSETS_DIR / "mechsoc_32.ico")
    if test:
        print("Starting UI in test mode at http://localhost:8080")
        ui.run(root, favicon=favicon_path)
    else:
        ui.run(root, native=True, title='Hello World', favicon=favicon_path)

def root():
    global df

    with ui.row().classes('w-full h-screen gap-6 flex-nowrap items-stretch'):
        with ui.column().classes('w-1/2 min-w-0'):
            ui.label('Hello World')

            spreadsheet = ui.aggrid.from_pandas(df).classes('max-h-40')
            spreadsheet.options["defaultColDef"] = {"editable": True, "filter": True, "resizable": True}
            spreadsheet.on('cellValueChanged', lambda: update_dataframe(spreadsheet))

            with ui.button_group():
                ui.button('clear', on_click=lambda: clear_spreadsheet(spreadsheet))
                ui.button('paste from clipboard', on_click=lambda: paste_spreadsheet_from_clipboard(spreadsheet))

        with ui.column().classes('w-1/2 min-w-0 h-full'):
            ui.label('Email Editor')
            with ui.button_group():
                ui.button('load template').on_click(lambda: load_template_dialog(subject_input, body_input))
                ui.button('save email as template').on_click(lambda: save_template(subject_input.value, body_input.value))
            with ui.card().classes('w-full h-full'):
                with ui.column().classes('w-full h-full gap-4'):
                    subject_input = ui.input(placeholder='Subject').classes('w-full').props('rounded outlined dense').on('update:model-value', lambda: save_local_template(subject_input.value, body_input.value))
                    body_toolbar = [
                        ['bold', 'italic', 'underline', 'strike'],
                        ['quote', 'unordered', 'ordered', 'outdent', 'indent'],
                        ['link', 'hr', 'undo', 'redo', 'fullscreen'],
                        [{
                            'label': 'Format',
                            'icon': 'format_size',
                            'list': 'no-icons',
                            'options': ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code']
                        }],
                        [{
                            'label': 'Align',
                            'icon': 'format_align_left',
                            'list': 'no-icons',
                            'options': ['left', 'center', 'right', 'justify']
                        }],
                        ['clean']
                    ]
                    body_input = (
                        ui.editor()
                        .classes('w-full h-full')
                        .props('rounded outlined dense')
                        .props(f":toolbar='{json.dumps(body_toolbar)}'")
                        .on('update:model-value', lambda: save_local_template(subject_input.value, body_input.value))
                    )
            with ui.button_group():
                ui.button('generate emails')
                ui.button('preview email').on_click(lambda: open_preview(preview_dialog, email_preview))

    with ui.dialog() as preview_dialog:
        with ui.card().classes('w-full h-3/4'):
            ui.label("Email Preview")
            email_preview = ui.html().classes('w-full h-full')
            preview_dialog.on('opened', lambda: email_preview.set_content(preview_email()))
            ui.button('close').on_click(lambda: preview_dialog.close())     


#def settings_page():
#    ui.label("Settings Page")
   

# ---- Graphical User Interface  Related Helper Functions ----

# -- Spreadsheet Management --

def clear_spreadsheet(spreadsheet):
    spreadsheet.options['rowData'] = []

def update_spreadsheet(spreadsheet):
    global df
    spreadsheet.options['rowData'] = df.to_dict(orient='records')
    scale_spreadsheet(spreadsheet)

def update_dataframe(spreadsheet):
    global df
    # extract the data from the spreadsheet and update the dataframe
    data = spreadsheet.options['rowData']
    df = pd.DataFrame(data)

def scale_spreadsheet(spreadsheet):
    global df
    # adjust the height of the spreadsheet to fit the number of rows, with a maximum height
    row_height = 35
    header_height = 35
    max_height = 1200
    new_height = min(header_height + row_height * len(df), max_height)
    spreadsheet.classes(f'max-h-{new_height}')

# -- template management --

def load_template_dialog(subject_input, body_input):
    filename = filedialog.askopenfilename(title="Select a template file", filetypes=[("MechSoc Email Template", "*.mset")])
    if filename:
        load_template(filename)
        insert_template_into_editor(subject_input, body_input)

def save_local_template(subject: str, body: str, sender: str = "", recipient: str = ""):
    global template
    template = email_builder.template(
        subject=normalize_liquid(subject),
        body=normalize_liquid(body),
        sender=sender,
        recipient=recipient,
    )



# ---- Dataframe Management ----

def initialise_dataframe():
    df = pd.DataFrame(columns=["name", "company", "email"])
    df = df._append({"name": "Alice", "company": "Company CO", "email": "alice@companyco.com"}, ignore_index=True)
    return df

def paste_spreadsheet_from_clipboard(spreadsheet):
    global df
    clipboard_data = pyperclip.paste()
    if not clipboard_data or not clipboard_data.strip():
        print("No data in clipboard")
        return

    try:
        new_df = _parse_clipboard_table(clipboard_data)
        if list(new_df.columns) != list(df.columns) and len(new_df.columns) == len(df.columns):
            new_df.columns = df.columns
        df = pd.concat([df, new_df], ignore_index=True)
        print(df)
        update_spreadsheet(spreadsheet)
    except Exception as e:
        print(f"Error parsing clipboard data: {e}")


def _parse_clipboard_table(raw_text: str) -> pd.DataFrame:
    text = raw_text.strip("\n\r\t ")
    sample = "\n".join(text.splitlines()[:10])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=["\t", ",", ";", "|"])
        sep = dialect.delimiter
    except csv.Error:
        sep = "\t"

    df_parsed = pd.read_csv(io.StringIO(text), sep=sep)
    if df_parsed.shape[1] == 1 and "\t" in text:
        df_parsed = pd.read_csv(io.StringIO(text), sep="\t")

    return df_parsed.dropna(how="all")

# ---- Email Template Management ----

template = None

def load_template(filename: str):
    global template
    template = email_builder.load(filename) 

def insert_template_into_editor(subject_input, body_input):
    global template
    if template:
        subject_input.value = template.subject
        body_input.value = template.body

def save_template(subject: str, body: str, sender: str = "", recipient: str = ""):
    global template
    template = email_builder.template(
        subject=normalize_liquid(subject),
        body=normalize_liquid(body),
        sender=sender,
        recipient=recipient,
    )

    file_path = filedialog.asksaveasfilename(title="Save template as", defaultextension=".mset", filetypes=[("MechSoc Email Template", "*.mset")])
    if file_path:
        template.export(file_path)



# ---- Email Generation ----

def preview_email():
    if template is None or df.empty:
        return "<em>No template or data available.</em>"

    sample_data = df.iloc[0].to_dict()
    body = normalize_liquid(template.body)
    subject = normalize_liquid(template.subject)
    eml = email_builder.Email(subject=subject, body=body)
    eml.parse_template(body, subject)
    body, subject = eml.render_content(sample_data)
    return f"<h1>{subject}</h1><div>{body}</div>"


def open_preview(preview_dialog, email_preview):
    email_preview.set_content(preview_email())
    preview_dialog.open()


def normalize_liquid(text: str) -> str:
    if not text:
        return text
    # Fix cases where the editor drops a closing brace: "{{ Name }" -> "{{ Name }}"
    return re.sub(r"\{\{\s*([^}]+?)\s*\}(?!\})", r"{{ \1 }}", text)



# ---- Application Entry Point ----

if __name__ in {"__main__", "__mp_main__"}:
    main()