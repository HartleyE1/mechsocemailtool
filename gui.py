import tkinter
from tkinter import messagebox, filedialog, ttk
from utils import paste_spreadsheet_data_to_csv
from pandastable import Table, TableModel
import pandas as pd
import io
import updater
import json

import os, sys

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def finish_message():
    messagebox.showinfo("Done", "Emails have been generated successfully!")

def start_gui(gen):
    root =  tkinter.Tk()
    root.title("MechSoc Email Tool")
    root.iconbitmap(resource_path("assets/mechsoc_32.ico"))
    root.iconphoto(True, tkinter.PhotoImage(file=resource_path("assets/mechsoc_256.png")))


    #window setup

    root.geometry("600x600")

    #bg = tkinter.PhotoImage( file = "mechsoc.png")

    #bg_label = tkinter.Label( root, image = bg)
    #bg_label.place(x = 0, y = 0 , relwidth=1, relheight=1)

    #############add elements here

    csv_var = tkinter.StringVar()
    output_var = tkinter.StringVar()
    template_var = tkinter.StringVar()

    #############version check button
    if updater.is_outdated():
        version_button = ttk.Button(root, text="Version Info •", command=open_version_window)
    else:
        version_button = ttk.Button(root, text="Version Info", command=open_version_window)
    version_button.place(relx=1.0, x=-10, y=10, anchor="ne")






    label = tkinter.Label(root, text="MechSoc Email Tool", font=("Arial", 16))
    label.pack(pady=20)



    frame1 = tkinter.Frame(root)
    frame1.pack(pady=10)    
    
    csv_entry_label = tkinter.Label(frame1, text="CSV String:")
    csv_frame = tkinter.Frame(frame1)
    csv_entry = tkinter.Entry(csv_frame, width=50, textvariable=csv_var)
    def _paste_and_update():
        s = paste_spreadsheet_data_to_csv()
        if not s:
            messagebox.showerror("Paste failed", "No data found on clipboard")
            return
        csv_var.set(s)
        update_table(preview_table, s)   # immediate update
    csv_paste_button = tkinter.Button(csv_frame, text="Paste from Spreadsheet", command=_paste_and_update)
    csv_entry_label.pack()
    csv_entry.pack(side=tkinter.LEFT, fill="x", expand=True)
    csv_paste_button.pack(side=tkinter.RIGHT, padx=10)
    csv_frame.pack(pady=10, fill="x")

    output_path_label = tkinter.Label(frame1, text="Output Folder:")
    output_frame = tkinter.Frame(frame1)
    output_entry = tkinter.Entry(output_frame, width=50, textvariable=output_var) 
    output_path_dialog_button = tkinter.Button(output_frame, text="Browse", command=lambda: output_var.set(filedialog.askdirectory()))
    output_path_label.pack()
    output_entry.pack(pady=10 , side=tkinter.LEFT, fill="x", expand=True)
    output_path_dialog_button.pack( side=tkinter.RIGHT, padx=10)
    output_frame.pack(pady=10, fill="x")
    
    template_path_label = tkinter.Label(frame1, text="Template Path:")
    template_frame = tkinter.Frame(frame1)
    template_entry = tkinter.Entry(template_frame, width=50, textvariable=template_var)
    open_template_button = tkinter.Button(template_frame, text="Browse", command=lambda: template_var.set(filedialog.askopenfilename(filetypes=[("EML files", "*.eml")])))
    template_path_label.pack() 
    template_entry.pack( side=tkinter.LEFT, fill="x", expand=True)
    open_template_button.pack(side=tkinter.RIGHT, padx=10)
    template_frame.pack(pady=10, fill="x")



    generate_emails_button = tkinter.Button(frame1, text="Generate Emails", command=lambda: gen(pass_selected_rows_only(preview_table, check1_var.get()), output_var.get(), template_var.get()))
    generate_emails_button.pack(pady=0)


    
    options_frame = tkinter.Frame(root, borderwidth=2, relief="groove", padx=10, pady=10)
    options_label = tkinter.Label(options_frame, text="Options")
    check1_var = tkinter.BooleanVar()
    check1 = tkinter.Checkbutton(options_frame, text="Generate emails for selected rows only", variable=check1_var)
    options_label.pack()
    check1.pack()
    options_frame.pack(pady=10)



    preview_table_frame = tkinter.Frame(root, padx=10, pady=10, )
    preview_table = Table(preview_table_frame, dataframe=pd.DataFrame(), read_only=False, style="Table")
    preview_table.redraw()
    preview_table_frame.pack(fill="both", expand=True, pady=20, padx=20)

    preview_table.show()







    ####################

    # attach trace AFTER preview_table exists
    csv_var.trace_add("write", lambda *args: update_table(preview_table, csv_var.get()))


    root.mainloop()

def open_version_window():
    with open("version_info.json", "r") as f:
        info = json.load(f)

    win = tkinter.Toplevel()
    win.title("Version Information")
    win.geometry("300x200")
    win.resizable(False, False)

    # Version label
    ttk.Label(win, text=f"Version: {info['version']}", font=("Segoe UI", 12)).pack(pady=5)
    ttk.Label(win, text=f"Date: {info['date']}", font=("Segoe UI", 10)).pack(pady=5)
    ttk.Label(win, text=f"Type: {info['type']}", font=("Segoe UI", 10)).pack(pady=5)

    # Spacer
    ttk.Label(win, text="").pack(pady=5)

    # Update button
    def do_update():
        updater.Update()
        ttk.Label(win, text="Update complete. Restart the app.", foreground="green").pack()

    ttk.Button(win, text="Update", command=do_update).pack(pady=10)



def update_table(table: Table, csv_string: str):
    print("Updating table...")
    s = (csv_string or "").strip()
    if not s:
        print("empty CSV string")
        return
    try:
        df = pd.read_csv(io.StringIO(s))
        print("Parsed DataFrame shape:", df.shape)
        print("Columns:", list(df.columns))
    except Exception as e:
        print(f"Failed to parse CSV data:\n{e}")
        messagebox.showerror("CSV parse error", f"Failed to parse CSV data:\n{e}")
        return

    table.updateModel(TableModel(df))
    table.autoResizeColumns()
    table.redraw()
    print("Table updated.")

def pass_selected_rows_only(table: Table, toggle: bool) -> pd.DataFrame:
    if not toggle:
        return table.model.df.copy()

    selected = table.getSelectedRowData()
    df = table.model.df

    # Handle case where nothing is selected
    if selected is None or (hasattr(selected, "empty") and selected.empty):
        return df.copy()

    # If it's a DataFrame already, just return a copy
    if isinstance(selected, pd.DataFrame):
        return selected.copy()

    # If it's a single integer index
    if isinstance(selected, int):
        selected_idx = [selected]
        return df.iloc[selected_idx].copy()

    # If it's a list of indices
    if isinstance(selected, (list, tuple)):
        return df.iloc[selected].copy()

    # Fallback: return whole df
    return df.copy()
