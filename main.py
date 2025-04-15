import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser

import json
import winreg
import os

import defaults

REGISTRY_PATH = r"SOFTWARE\Roblox\RobloxStudio\Themes\Dark\ScriptEditorColors\SyntaxHighlighting\custom" # default registry key

currentConfiguration = defaults.defaultConfiguration.copy()

color_images = []
# helper functions

def reg_to_dict(file):
    data = {}
    for line in file:
        line = line.strip()
        if line.startswith('"') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip('"')
            if value.startswith('"') and value.endswith('"'):
                value = value.strip('"')
            elif value.startswith('dword:'):
                value = int(value[6:], 16)
            data[key] = value
    return data

def read_registry_configuration(update: bool = True):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ) as key:
            num_values = winreg.QueryInfoKey(key)[1]
            registry_data = {}
            
            for i in range(num_values):
                valueName, valueData, _ = winreg.EnumValue(key, i)
                registry_data[valueName] = valueData

        if update:
            currentConfiguration.update(registry_data)
            print("Loaded configuration from registry: ", currentConfiguration)
            update_status("Loaded configuration from registry.")
            update_list()
        else:
            return registry_data

    except FileNotFoundError:
        messagebox.showwarning(f"The registry key \"{REGISTRY_PATH}\" wasn't found!")
        update_status("Failed loading configuration from registry. You may load a .json theme file if necessary.")
    except Exception as e:
        messagebox.showerror("Error", e)
        exit()

def new_file():
    global currentConfiguration
    currentConfiguration = defaults.defaultConfiguration.copy()
    
    update_status("Created new file.")
    update_list()

def open_theme():
    global currentConfiguration
    
    path = filedialog.askopenfilename(
        title="Open Theme File",
        filetypes=[("Theme Files", "*.reg *.json"), ("Registration Files", "*.reg"), ("JSON Files", "*.json")]
    )
    if path:
        try:
            with open(path, "r") as f:
                if path.endswith(".json"):
                    data = json.load(f)
                else:
                    data = reg_to_dict(f)
                    
            # check integrity
            # first off, if the data is a dict
            
            if not isinstance(data, dict):
                messagebox.showerror("Error", "The theme file may be incorrect. Verify its' integrity and contents.")
                update_status("Attempted importing incompatible file.")
                raise ValueError("Attempted importing incompatible file. It does not appear to be a dict.")
            
            expected_keys = set(defaults.defaultConfiguration.keys())
            imported_keys = set(data.keys())
            
            missing_keys = expected_keys - imported_keys
            extra_keys = imported_keys - expected_keys
            
            # if any keys are missing, use the default configuration values and inform user
            # if any key is extra, assume the file is incorrect and don't import
            
            if missing_keys:
                messagebox.showinfo("Info", "Some keys seem to be missing. The default values will be used as a replacement.")
            
            if extra_keys:
                messagebox.showerror("Error", "The JSON theme file contains extra keys. Verify its' integrity and contents.")
                update_status("Attempted importing incompatible JSON file.")
                raise Exception("Attempted importing incompatible JSON file. It contains extra keys.")
            
            currentConfiguration = data
            
            for key, value in data.items():
                currentConfiguration[key] = value

            update_status(f"Loaded file {path}")
            print(f"cc: {currentConfiguration}")
            update_list()
            
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

def save_theme(): # save currentconfig 
    path = filedialog.asksaveasfilename(
        title="Save Current Configuration",
        defaultextension=".json",
        filetypes=[("Theme Files", "*.reg *.json"), ("Registration Files", "*.reg"), ("JSON Files", "*.json")]
    )
    if path:
        try:
            if path.lower().endswith(".json"):
                with open(path, "w") as f:
                    json.dump(currentConfiguration, f, indent=4)
            elif path.lower().endswith(".reg"):
                regContent = "Windows Registry Editor Version 5.00\n\n"
                regContent += f"[HKEY_CURRENT_USER\\{REGISTRY_PATH}]\n"
                for key, value in currentConfiguration.items():
                    regContent += f'"{key}"="{value}"\n'
                with open(path, "w") as f:
                    f.write(regContent)
            print(f"Saved current configuration to {path}.")
            update_status(f"Saved to {path}.")
        except Exception as e:
            print(f"Error saving file: {e}")

def save_to_registry():
    if not os.path.exists("./registry_backup.reg"):
        choice = messagebox.askyesnocancel("WARNING", "You haven't backed up the registry yet. Do you want to create a backup? (recommended)")
    
        if choice == True: # yes
            do_registry_backup()
        elif choice == False:
            print("Don't do the thing")
        elif choice == None:
            print("do nothing")
            
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
            for valueName, valueData in currentConfiguration.items():
                winreg.SetValueEx(key, valueName, 0, winreg.REG_SZ, valueData)
        update_status("Configuration applied to registry. Restart studio to finalize.")
        print("Registry updated:", currentConfiguration)
    except Exception as e:
        messagebox.showerror("Error", e)
    
def do_registry_backup():
    registryData = read_registry_configuration(False)
    if not registryData:
        print("No data found to back up!")
        return

    backupFile = "registry_backup.reg"
    regContent = "Windows Registry Editor Version 5.00\n\n"
    regContent += f"[HKEY_CURRENT_USER\\{REGISTRY_PATH}]\n"

    for valueName, valueData in registryData.items():
        if isinstance(valueData, str):
            valueData = f'"{valueData}"'
        elif isinstance(valueData, int):
            valueData = f"dword:{valueData:08x}"
        elif isinstance(valueData, bytes):
            valueData = f"hex:{','.join(f'{b:02x}' for b in valueData)}"

        regContent += f'"{valueName}"={valueData}\n'

    try:
        with open(backupFile, 'w') as file:
            file.write(regContent)
        print(f"Registry key successfully backed up to {backupFile}")
        update_status(f"Backup made: {backupFile}")
    except Exception as e:
        print(f"Error writing to {backupFile}: {e}")
        
def exit_app():
    root.quit()

root = tk.Tk()
root.title("Studio Themes")
root.resizable(False, False)
root.geometry("800x600")

# menu bar
menubar = tk.Menu(root)

# file menu
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="New", command=new_file)
file_menu.add_command(label="Open", command=open_theme)
file_menu.add_command(label="Save", command=save_theme)
file_menu.add_command(label="-- Registry --", state="disabled")
file_menu.add_command(label="Load", command=read_registry_configuration)
file_menu.add_command(label="Apply", command=save_to_registry)
file_menu.add_command(label="Backup", command=do_registry_backup)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_app)
menubar.add_cascade(label="File", menu=file_menu)

# status bar
status_bar = tk.Frame(root, height=30, bg="white smoke")
status_bar.pack(side="bottom", fill="x", pady=2)

status_label = tk.Label(status_bar, text="Ready", bg="white smoke", anchor="w")
status_label.pack(fill="x", padx=10)

def update_status(message):
    status_label.config(text=message)

# colors list frame
frame = tk.Frame(root)
frame.pack(pady=20, padx=20, fill="both", expand=True)

list_frame = tk.Frame(frame)
list_frame.pack(side="left", fill="y")



# planting the tree 🌳
tree = ttk.Treeview(list_frame, columns=("Name",), show="tree headings", height=10)
tree.heading("#0", text="Color")
tree.column("#0", width=50, anchor="center", minwidth=50)
tree.heading("Name", text="Element Name")
tree.column("Name", width=200, anchor="w", stretch=False)
tree.pack(side="left", fill="y")

scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.config(yscrollcommand=scrollbar.set)

spacer = tk.Frame(frame)
spacer.pack(side="left", fill="both", expand=True)

# events 
# disable resizing
def disable_column_resize(event):
    if tree.identify_region(event.x, event.y) == "separator":
        return "break"

tree.bind("<Button-1>", disable_column_resize)

# on double click
def color_double_click(_):
    global currentConfiguration
    
    selection = tree.selection()
    if selection:
        selectionText = tree.item(selection, "values")[0]
        registryKeyName = defaults.registryNames[selectionText]
        print(registryKeyName)
        
        # color wheel
        newColor = colorchooser.askcolor(title=selectionText, initialcolor=currentConfiguration[registryKeyName])[1]
        if newColor:
            currentConfiguration[registryKeyName] = newColor
            update_list()

tree.bind("<Double-1>", color_double_click)

def create_color_square(color):
    img = tk.PhotoImage(width=16, height=16)
    img.put(color, to=(0, 0, 16, 16))
    return img

def update_list(): 
    for c in tree.get_children():
        tree.delete(c)
    
    color_images.clear()
    
    for key, color in currentConfiguration.items():
        img = create_color_square(color)
        color_images.append(img)
        tree.insert("", tk.END, text="", image=img, values=(defaults.studioNames[key],))

read_registry_configuration()

style = ttk.Style()
style.configure("Treeview", rowheight=20)
style.configure("Treeview.Item", padding=(0, 0))

root.config(menu=menubar)
root.mainloop()