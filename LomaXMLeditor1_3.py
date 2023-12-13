#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk, PanedWindow
import xml.etree.ElementTree as ET

class NewElementDialog(tk.simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Select tag:").grid(row=0)
        tk.Label(master, text="Enter text:").grid(row=1)

        self.tag_var = tk.StringVar(master)
        self.tag_combo = ttk.Combobox(master, textvariable=self.tag_var, width=70)  # Increased width
        self.tag_combo['values'] = list(existing_tags)
        self.tag_combo.grid(row=0, column=1)
        self.text_var = tk.StringVar(master)
        self.text_entry = tk.Entry(master, textvariable=self.text_var, width=70)
        self.text_entry.grid(row=1, column=1)

        return self.tag_combo  # initial focus

    def apply(self):
        tag = self.tag_var.get()
        text = self.text_var.get()
        self.result = (tag, text)


def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
    if filename:
        tree = ET.parse(filename)
        root = tree.getroot()
        clear_treeview()
        populate_treeview(root, '')
        update_text_output(root)
        global xml_tree
        xml_tree = tree

existing_tags = []

def populate_treeview(element, parent, text_pos=0):
    # Add the tag to existing_tags if it's not already in the list
    if element.tag not in existing_tags:
        existing_tags.append(element.tag)

    node_id = treeview.insert(parent, 'end', text=element.tag, open=True)
    if element.text:
        text = element.text.strip()
        if text:
            text_id = treeview.insert(node_id, 'end', text=text)
            treeview.item(text_id, tags=('text',))
            text_positions[text_id] = (text_pos, text_pos + len(text))
            text_pos += len(text)

    for child in element:
        text_pos = populate_treeview(child, node_id, text_pos)

    return text_pos

def update_text_output(element):
    text_output.delete(1.0, tk.END)
    append_text_output(element)

def append_text_output(element, depth=0):
    if element.text:
        text = element.text.strip()
        if text:
            text_output.insert(tk.END, text + '\n', 'blue_text')
    
    for child in element:
        append_text_output(child, depth + 1)

def clear_treeview():
    for item in treeview.get_children():
        treeview.delete(item)

def edit_node():
    selected_item = treeview.selection()
    if selected_item:
        text = simpledialog.askstring("Edit text", "Enter text:", initialvalue=treeview.item(selected_item[0], 'text'))
        if text is not None:
            treeview.item(selected_item[0], text=text)
            update_text_output(xml_tree.getroot())

def save_file():
    try:
        root = rebuild_tree('', xml_tree.getroot())
        xml_tree._setroot(root)
        xml_tree.write('modified.xml')
        messagebox.showinfo("Success", "File saved successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Error saving file: {e}")

def rebuild_tree(parent_id, element):
    new_element = ET.Element(treeview.item(parent_id, 'text'))
    for child_id in treeview.get_children(parent_id):
        child_text = treeview.item(child_id, 'text')
        if child_text.startswith('text: '):
            new_element.text = child_text[6:]
        else:
            new_element.append(rebuild_tree(child_id, element))
    return new_element

def on_tree_select(event):
    selected_items = treeview.selection()
    if selected_items and treeview.item(selected_items[0], 'tags'):
        start_pos, end_pos = text_positions.get(selected_items[0], (0, 0))
        text_output.tag_remove('sel', '1.0', tk.END)
        text_output.tag_add('sel', f'1.0+{start_pos}c', f'1.0+{end_pos}c')
        text_output.see(f'1.0+{start_pos}c')

def add_new_element():
    dialog = NewElementDialog(root)
    result = dialog.result

    if result:
        new_tag, new_text = result
        if new_tag and new_text:
            insert_new_element(new_tag, new_text)
            
def insert_new_element(tag, text):
    selected_item = treeview.selection()
    if selected_item:
        parent_id = selected_item[0]
    else:
        parent_id = ''  # Insert at the root if no selection

    new_node_id = treeview.insert(parent_id, 'end', text=tag, open=True)
    treeview.insert(new_node_id, 'end', text=text, tags=('text',))

# Set up the main window
root = tk.Tk()
root.title("XML Tree Editor")

# Create a paned window
paned_window = PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

# Create a treeview in the left pane
treeview = ttk.Treeview(paned_window)
treeview.bind('<<TreeviewSelect>>', on_tree_select)
paned_window.add(treeview, width=300)

# Create a scrollbar for the treeview
scrollbar_treeview = ttk.Scrollbar(treeview, orient="vertical", command=treeview.yview)
scrollbar_treeview.pack(side=tk.RIGHT, fill="y")
treeview.configure(yscrollcommand=scrollbar_treeview.set)

# Configure tag for text items
treeview.tag_configure('text', foreground='blue')

# Create a frame for the text area and its scrollbar in the right pane
text_frame = tk.Frame(paned_window)
paned_window.add(text_frame, width=300)

# Create a text area for the text-only output
text_output = tk.Text(text_frame, height=20, width=80)
text_output.tag_configure('blue_text', foreground='blue')
text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a scrollbar for the text area
scrollbar_text_output = ttk.Scrollbar(text_frame, orient="vertical", command=text_output.yview)
scrollbar_text_output.pack(side=tk.RIGHT, fill="y")
text_output.configure(yscrollcommand=scrollbar_text_output.set)

# Create buttons
button_frame = tk.Frame(root)
button_frame.pack(side=tk.BOTTOM, fill=tk.X)

browse_button = tk.Button(button_frame, text="Browse XML File", command=browse_file)
browse_button.pack(side=tk.LEFT)
edit_button = tk.Button(button_frame, text="Edit Node", command=edit_node)
edit_button.pack(side=tk.LEFT)
add_element_button = tk.Button(button_frame, text="Add New Element", command=add_new_element)
add_element_button.pack(side=tk.LEFT)
save_button = tk.Button(button_frame, text="Save XML File", command=save_file)
save_button.pack(side=tk.RIGHT)

text_positions = {}  # Global dictionary to map treeview text to positions in text_output

root.mainloop()
