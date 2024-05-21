import os
import json
import mimetypes
import stat
import time
import win32api
import win32con
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from snapshot import create_snapshot, save_snapshot, load_snapshot
from compare import compare_directories
from about import about_fw
from ads import list_ads_files


class Window():
    def __init__(self, root):
        self.root = root
        self.root.title("Folder watcher")
        self.root.geometry('800x450')
        self.root.resizable(width=True, height=True)
        self.root.configure(bg='white')

        self.use_ads = tk.BooleanVar(value=False)
        self.show_size = tk.BooleanVar(value=True)
        self.show_type = tk.BooleanVar(value=True)
        self.show_attributes = tk.BooleanVar(value=True)
        self.show_last_modified = tk.BooleanVar(value=True)
        self.last_directory1 = tk.StringVar()
        self.last_directory2 = tk.StringVar()
        self.directory_label1 = tk.StringVar(value="Directory 1")
        self.directory_label2 = tk.StringVar(value="Directory 2")
        self.language = tk.StringVar(value="English")
        self.snapshot = None
        self.target_treeview = None

        self.translations = {}
        self.available_languages = self.load_available_languages()
        self.load_translations(self.language.get())

        self.create_widgets()
        self.create_menu()
        self.setup_traces()

    def load_available_languages(self):
        languages = {}
        translation_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.startswith('translations_') and f.endswith('.json')]
        for file in translation_files:
            lang_code = file.split('_')[1].split('.')[0]
            languages[lang_code.capitalize()] = file
        return languages

    def load_translations(self, language):
        filename = self.available_languages.get(language.lower().capitalize())
        if filename:
            filepath = os.path.join(os.path.dirname(__file__), filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    self.translations = json.load(file)
            except FileNotFoundError:
                messagebox.showerror("Error", f"Translation file {filename} not found.")
                self.translations = {}

    def translate(self, text):
        return self.translations.get(text, text)

    def create_snapshot_action(self):
        if self.last_directory1.get():
            self.snapshot = create_snapshot(self.last_directory1.get(), self.use_ads.get())
            snapshot_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if snapshot_file:
                save_snapshot(self.snapshot, snapshot_file)
                messagebox.showinfo("Snapshot Created", "Snapshot has been successfully created and saved.")
        else:
            messagebox.showerror(self.translate("No Directory Selected"), self.translate("Please select a directory first."))

    def load_snapshot_action(self):
        snapshot_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if snapshot_file:
            try:
                with open(snapshot_file, 'r') as file:
                    self.snapshot = json.load(file)
                messagebox.showinfo(self.translate("Snapshot Loaded"), self.translate("Snapshot has been successfully loaded."))
                self.update_treeview_with_snapshot(self.target_treeview, self.snapshot)
            except json.JSONDecodeError:
                messagebox.showerror(self.translate("Invalid JSON"), self.translate("The file is not a valid JSON file."))
            except Exception as e:
                messagebox.showerror(self.translate("Error"), f"{self.translate('An error occurred')}: {e}")
        else:
            messagebox.showinfo(self.translate("Loading Cancelled"), self.translate("No file was selected."))

    def update_comparison_results(self, only_in1_files, only_in2_files, modified_files, only_in1_dirs, only_in2_dirs, size_diff_dirs):
        self.list_files(self.file_tree1, self.last_directory1.get())
        for child in self.file_tree1.get_children():
            item = self.file_tree1.item(child)
            filename = item['values'][0]
            filepath = os.path.join(self.last_directory1.get(), filename)
            tags = ()
            if filename in only_in1_files:
                tags = ('deleted',)
            elif filename in only_in2_files:
                tags = ('new',)
            elif filename in modified_files:
                file_info = modified_files[filename]
                if file_info['size']:
                    tags += ('modified',)
                if file_info['attributes']:
                    tags += ('attributes_modified',)
                if file_info['last_modified']:
                    tags += ('last_modified',)
            self.file_tree1.item(child, tags=tags)
            
        self.file_tree1.tag_configure('new', background='lightgreen')
        self.file_tree1.tag_configure('deleted', background='brown1')
        self.file_tree1.tag_configure('modified', background='burlywood3')
        self.file_tree1.tag_configure('attributes_modified', background='lightblue')
        self.file_tree1.tag_configure('last_modified', background='lightpink')

        self.list_files(self.file_tree2, self.last_directory2.get())
        for child in self.file_tree2.get_children():
            item = self.file_tree2.item(child)
            filename = item['values'][0]
            filepath = os.path.join(self.last_directory2.get(), filename)
            tags = ()
            if filename in only_in2_files:
                tags = ('new',)
            elif filename in only_in1_files:
                tags = ('deleted',)
            elif filename in modified_files:
                file_info = modified_files[filename]
                if file_info['size']:
                    tags += ('modified',)
                if file_info['attributes']:
                    tags += ('attributes_modified',)
                if file_info['last_modified']:
                    tags += ('last_modified',)
            self.file_tree2.item(child, tags=tags)
            
        self.file_tree2.tag_configure('new', background='lightgreen')
        self.file_tree2.tag_configure('deleted', background='brown1')
        self.file_tree2.tag_configure('modified', background='burlywood3')
        self.file_tree2.tag_configure('attributes_modified', background='lightblue')
        self.file_tree2.tag_configure('last_modified', background='lightpink')

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label=self.translate("About Folder Watcher"), command=self.btn_about_fw)
        menubar.add_cascade(label=self.translate("About"), menu=filemenu)

        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translate("Language"), menu=language_menu)

        for lang in self.available_languages.keys():
            language_menu.add_command(label=lang, command=lambda l=lang: self.update_language(l))

    def btn_about_fw(self):
        about_fw(self.root, self.language, self.translations)

    def update_language(self, lang):
        self.language.set(lang)
        self.load_translations(lang)
        self.update_display()

    def create_widgets(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        style = ttk.Style()
        style.configure('Custom.TButton', font=('Helvetica', 14))
        style.configure('Custom.TLabel', font=('Helvetica', 14))

        left_canvas = tk.Canvas(self.root, bg='white', width=100)
        left_canvas.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.compare_btn = ttk.Button(left_canvas, text=self.translate("Compare"), command=self.btn1_click, style='Custom.TButton', takefocus=0)
        self.compare_btn.pack(pady=10)
        self.ads_check = tk.Checkbutton(left_canvas, text=self.translate("Ads"), variable=self.use_ads, background='white', takefocus=0)
        self.ads_check.pack(pady=10)

        self.create_snapshot_btn = ttk.Button(left_canvas, text=self.translate("Create Snapshot"), command=self.create_snapshot_action, style='Custom.TButton', takefocus=0)
        self.create_snapshot_btn.pack(pady=10)
        self.load_snapshot_btn = ttk.Button(left_canvas, text=self.translate("Load Snapshot"), command=self.load_snapshot_action, style='Custom.TButton', takefocus=0)
        self.load_snapshot_btn.pack(pady=10)

        frame1 = ttk.Frame(self.root)
        frame1.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        frame1.grid_columnconfigure(0, weight=1)
        self.directory1_entry = ttk.Entry(frame1, textvariable=self.last_directory1)
        self.directory1_entry.grid(row=0, column=0, sticky='ew')
        self.directory1_entry.bind('<Return>', lambda event: self.update_directory(self.file_tree1, self.last_directory1.get()))
        self.directory1_button = ttk.Button(frame1, text='^', command=lambda: self.select_directory(True), style='Custom.TButton', takefocus=0)
        self.directory1_button.grid(row=0, column=1)

        frame2 = ttk.Frame(self.root)
        frame2.grid(row=0, column=2, sticky='ew', padx=5, pady=5)
        frame2.grid_columnconfigure(0, weight=1)
        self.directory2_entry = ttk.Entry(frame2, textvariable=self.last_directory2)
        self.directory2_entry.grid(row=0, column=0, sticky='ew')
        self.directory2_entry.bind('<Return>', lambda event: self.update_directory(self.file_tree2, self.last_directory2.get()))
        self.directory2_button = ttk.Button(frame2, text='^', command=lambda: self.select_directory(False), style='Custom.TButton', takefocus=0)
        self.directory2_button.grid(row=0, column=1)

        checkbox_frame = tk.Frame(self.root, background='white')
        checkbox_frame.grid(row=1, column=1, columnspan=2, sticky='w', pady=5)
        
        self.show_size_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Size"), variable=self.show_size, background='white', takefocus=0)
        self.show_size_btn.pack(side=tk.LEFT, padx=5)
        self.show_type_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Type"), variable=self.show_type, background='white', takefocus=0)
        self.show_type_btn.pack(side=tk.LEFT, padx=5)
        self.show_attributes_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Attributes"), variable=self.show_attributes, background='white', takefocus=0)
        self.show_attributes_btn.pack(side=tk.LEFT, padx=5)
        self.show_last_modified_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Last Modified"), variable=self.show_last_modified, background='white', takefocus=0)
        self.show_last_modified_btn.pack(side=tk.LEFT, padx=5)

        self.setup_treeview()

        self.target_treeview_selector = ttk.Combobox(left_canvas, values=["Treeview 1", "Treeview 2"], style='Custom.TCombobox')
        self.target_treeview_selector.pack(pady=10)
        self.target_treeview_selector.bind("<<ComboboxSelected>>", self.select_target_treeview)

    def update_directory(self, treeview, directory):
        if os.path.isdir(directory):
            self.list_files(treeview, directory)
        else:
            messagebox.showerror(self.translate("Error"), self.translate("Invalid directory path"))

    def select_target_treeview(self, event):
        choice = self.target_treeview_selector.get()
        if choice == "Treeview 1":
            self.target_treeview = self.file_tree1
        elif choice == "Treeview 2":
            self.target_treeview = self.file_tree2

    def setup_treeview(self):
        self.columns = [
            self.translate("File Name"),
            self.translate("Size"),
            self.translate("Type"),
            self.translate("Attributes"),
            self.translate("Last Modified")
        ]
        self.file_tree1 = ttk.Treeview(self.root, columns=self.columns, show="headings")
        self.file_tree2 = ttk.Treeview(self.root, columns=self.columns, show="headings")
        self.update_column_visibility()
        self.file_tree1.grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
        self.file_tree2.grid(row=2, column=2, sticky='nsew', padx=5, pady=5)

        self.root.grid_rowconfigure(2, weight=1)  # Ensure the row containing treeviews expands
        self.root.grid_rowconfigure(1, weight=0)  # Ensure the row containing checkboxes does not expand

    def select_directory(self, is_first):
        directory = filedialog.askdirectory()
        if directory:
            if is_first:
                self.last_directory1.set(directory)
                self.list_files(self.file_tree1, directory)
            else:
                self.last_directory2.set(directory)
                self.list_files(self.file_tree2, directory)

    def list_files(self, treeview, directory):
        treeview.delete(*treeview.get_children())
        if directory:
            for item in os.scandir(directory):
                if self.use_ads.get() and not item.is_dir():
                    ads_files = list_ads_files(item.path)
                    for ads_file, size in ads_files:
                        self.insert_file_item(treeview, ads_file, size, "ADS")
                self.insert_file_item(treeview, item)

    def insert_file_item(self, treeview, item, item_size=None, item_type=""):
        if isinstance(item, os.DirEntry):
            display_text = item.name
            item_path = item.path
            size_text = ""
            type_text = ""
            attributes_text = self.get_file_attributes(item_path)
            last_modified_text = self.get_last_modified(item_path)
            if item.is_dir():
                type_text = self.translate("Folder")
            else:
                file_size = os.path.getsize(item_path)
                mime_type, _ = mimetypes.guess_type(item_path)
                file_type = self.get_file_description(mime_type)
                size_text = f"{file_size} bytes"
                type_text = file_type
        else:
            file_name, stream_name = item.rsplit(':', 1)
            stream_name = stream_name.replace('$DATA', '').strip()
            display_text = f"{os.path.basename(file_name)}:{stream_name}"
            size_text = f"{item_size} bytes"
            type_text = "ADS File" if ':' in item else "File"
            attributes_text = ""
            last_modified_text = ""

        values = [display_text, size_text, type_text, attributes_text, last_modified_text]
        tags = ()
        if 'ADS' in item_type:
            tags = ('ads_file_pre',)
        treeview.insert("", 'end', values=values, tags=tags)

    def get_file_description(self, mime_type):
        descriptions = {
            'image': self.translate("Image"),
            'audio': self.translate("Audio"),
            'video': self.translate("Video"),
            'application/pdf': self.translate("PDF Document"),
            'application/msword': self.translate("Word Document"),
            'application/vnd.ms-excel': self.translate("Excel Spreadsheet"),
            'application/vnd.ms-powerpoint': self.translate("PowerPoint Presentation"),
            'application/zip': self.translate("ZIP Archive"),
            'application/x-rar-compressed': self.translate("RAR Archive"),
            'application/gzip': self.translate("GZip Archive"),
            'application/x-7z-compressed': self.translate("7z Archive"),
            'application': self.translate("Application"),
            'text': self.translate("Document")
        }
        for key, value in descriptions.items():
            if mime_type and key in mime_type:
                return value
        return self.translate("Unknown")

    def get_file_attributes(self, path):
        attributes = []
        attrs = win32api.GetFileAttributes(path)

        if attrs & win32con.FILE_ATTRIBUTE_ARCHIVE:
            attributes.append('A')
        else:
            attributes.append('-')
            
        if attrs & win32con.FILE_ATTRIBUTE_HIDDEN:
            attributes.append('H')
        else:
            attributes.append('-')
            
        if attrs & win32con.FILE_ATTRIBUTE_SYSTEM:
            attributes.append('S')
        else:
            attributes.append('-')
            
        if attrs & win32con.FILE_ATTRIBUTE_READONLY:
            attributes.append('R')
        else:
            attributes.append('-')

        return ''.join(attributes)

    def get_last_modified(self, path):
        last_modified_timestamp = os.path.getmtime(path)
        last_modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_timestamp))
        return last_modified_time

    def update_column_visibility(self):
        columns_to_display = [self.translate("File Name")]
        if self.show_size.get():
            columns_to_display.append(self.translate("Size"))
        if self.show_type.get():
            columns_to_display.append(self.translate("Type"))
        if self.show_attributes.get():
            columns_to_display.append(self.translate("Attributes"))
        if self.show_last_modified.get():
            columns_to_display.append(self.translate("Last Modified"))

        for tree in [self.file_tree1, self.file_tree2]:
            tree["columns"] = columns_to_display
            for col in columns_to_display:
                tree.heading(col, text=col)
                tree.column(col, width=100, minwidth=25, stretch=tk.YES)

            current_columns = set(tree["columns"])
            for col in list(current_columns):
                if col not in columns_to_display:
                    tree.column(col, width=0, minwidth=0, stretch=tk.NO)

            if tree == self.file_tree1 and self.last_directory1.get():
                self.list_files(self.file_tree1, self.last_directory1.get())
            elif tree == self.file_tree2 and self.last_directory2.get():
                self.list_files(self.file_tree2, self.last_directory2.get())

    def setup_traces(self):
        self.show_size.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_type.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_attributes.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_last_modified.trace_add('write', lambda *args: self.update_column_visibility())
        self.language.trace_add('write', lambda *args: self.update_display())
        self.use_ads.trace_add('write', lambda *args: self.update_display())

    def update_display(self):
        self.compare_btn.config(text=self.translate("Compare"))
        self.ads_check.config(text=self.translate("Ads"))
        self.create_snapshot_btn.config(text=self.translate("Create Snapshot"))
        self.load_snapshot_btn.config(text=self.translate("Load Snapshot"))
        self.show_size_btn.config(text=self.translate("Show Size"))
        self.show_type_btn.config(text=self.translate("Show Type"))
        self.show_attributes_btn.config(text=self.translate("Show Attributes"))
        self.show_last_modified_btn.config(text=self.translate("Show Last Modified"))

        # Recreate the menu to update the translations
        self.create_menu()
        self.update_column_visibility()

    def btn1_click(self):
        if self.last_directory1.get() and self.last_directory2.get():
            size_diff_files, only_in1_files, only_in2_files, only_in1_dirs, only_in2_dirs, size_diff_dirs = compare_directories(self.last_directory1.get(), self.last_directory2.get())
            self.update_comparison_results(only_in1_files, only_in2_files, size_diff_files, only_in1_dirs, only_in2_dirs, size_diff_dirs)
        else:
            messagebox.showinfo(self.translate("Error"), self.translate("Both directories must be selected before comparing"))

    def update_treeview_with_snapshot(self, treeview, snapshot):
        treeview.delete(*treeview.get_children())
        for rel_path, details in snapshot.items():
            file_name = os.path.basename(rel_path)
            file_size = details.get('size', 'Unknown size')
            file_type = details.get('type', 'Unknown type')
            attributes = self.get_file_attributes(file_name)
            last_modified = self.get_last_modified(file_name)
            treeview.insert("", 'end', values=(file_name, f"{file_size} bytes", file_type, attributes, last_modified))

    def update_treeview_with_differences(self, treeview, directory, diff_results):
        size_diff_files, only_in1_files, only_in2_files, only_in1_dirs, only_in2_dirs, size_diff_dirs = diff_results
        self.list_files(treeview, directory)

        treeview.tag_configure('size_diff', background='lightgreen')
        treeview.tag_configure('only_in_one', background='lightblue')
        treeview.tag_configure('ads_file_post', background='orange')

        for child in treeview.get_children():
            item = treeview.item(child)
            filename = item['values'][0]
            current_tags = list(item['tags'])

            if filename in size_diff_files or filename in size_diff_dirs:
                current_tags.append('size_diff')
            if filename in only_in1_files or filename in only_in2_files or filename in only_in1_dirs or filename in only_in2_dirs:
                current_tags.append('only_in_one')
            if 'ads_file_pre' in current_tags:
                current_tags.append('ads_file_post')
            
            treeview.item(child, tags=tuple(current_tags))


if __name__ == "__main__":
    root = tk.Tk()
    app = Window(root)
    root.mainloop()
