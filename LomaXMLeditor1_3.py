#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk, PanedWindow
from lxml import etree as ET

class NewElementDialog(tk.simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Select tag:").grid(row=0)
        tk.Label(master, text="Enter text:").grid(row=1)

        self.tag_var = tk.StringVar(master)
        self.tag_combo = ttk.Combobox(master, textvariable=self.tag_var, width=50)
        self.tag_combo['values'] = list(existing_tags)
        self.tag_combo.grid(row=0, column=1)
        self.text_var = tk.StringVar(master)
        self.text_entry = tk.Entry(master, textvariable=self.text_var, width=50)
        self.text_entry.grid(row=1, column=1)

        return self.tag_combo  # initial focus

    def apply(self):
        tag = self.tag_var.get()
        text = self.text_var.get()
        self.result = (tag, text)

def add_new_element():
    tag_selection = list(existing_tags)
    if not tag_selection:
        messagebox.showinfo("Info", "No existing tags to base the new element on.")
        return

    dialog = NewElementDialog(root)
    result = dialog.result

    if result:
        new_tag, new_text = result
        if new_tag and new_text:
            insert_new_element(new_tag, new_text)

def insert_new_element(tag, text):
    selected_item = treeview.selection()
    parent_id = selected_item[0] if selected_item else ''
    new_node_id = treeview.insert(parent_id, 'end', text=tag, open=True)
    treeview.insert(new_node_id, 'end', text=text, tags=('text',))
    treeview_to_xml_mapping[new_node_id] = ET.Element(tag)
    treeview_to_xml_mapping[new_node_id].text = text
    update_text_output(xml_tree.getroot())

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
    if filename:
        global xml_tree
        with open(filename, 'r') as file:
            xml_tree = ET.parse(file)
        root = xml_tree.getroot()
        clear_treeview()
        populate_treeview(root, '')
        update_text_output(root)

existing_tags = set()
text_positions = {}  # Global dictionary to map treeview text to positions in text_output
treeview_to_xml_mapping = {}

def populate_treeview(element, parent, text_pos=0, depth=0):
    node_id = treeview.insert(parent, 'end', text=element.tag, open=depth < 1)
    treeview_to_xml_mapping[node_id] = element
    existing_tags.add(element.tag)

    if element.text and element.text.strip():
        text = element.text.strip()
        text_id = treeview.insert(node_id, 'end', text=text, tags=('text',))
        start_pos = f'1.0+{text_pos}c'
        end_pos = f'1.0+{text_pos + len(text)}c'
        text_positions[text_id] = (start_pos, end_pos)
        text_pos += len(text) + 1

    for child in element:
        child_id = populate_treeview(child, node_id, text_pos, depth + 1)
        treeview_to_xml_mapping[child_id] = child

    return node_id

def update_text_output(element):
    text_output.delete(1.0, tk.END)
    append_text_output(element)

def append_text_output(element, depth=0):
    if element.text and element.text.strip():
        text = element.text.strip()
        text_output.insert(tk.END, text + '\n', 'blue_text')

    for child in element:
        append_text_output(child, depth + 1)

def clear_treeview():
    for item in treeview.get_children():
        treeview.delete(item)
    treeview_to_xml_mapping.clear()

def update_xml_element_from_treeview(item_id, new_text):
    xml_element = treeview_to_xml_mapping.get(item_id)
    if xml_element is not None:
        xml_element.text = new_text

def edit_node():
    selected_item = treeview.selection()
    if selected_item:
        item_id = selected_item[0]
        current_text = treeview.item(item_id, 'text')
        new_text = simpledialog.askstring("Edit text", "Enter new text:", initialvalue=current_text)
        if new_text and new_text != current_text:
            treeview.item(item_id, text=new_text)
            update_xml_element_from_treeview(item_id, new_text)
            update_text_output(xml_tree.getroot())

def sync_treeview_to_xml(treeview_item_id, xml_parent_element):
    for child_id in treeview.get_children(treeview_item_id):
        child_tag, child_text = treeview.item(child_id, "text"), treeview.item(child_id, "values")
        if 'text' in treeview.item(child_id, 'tags'):
            # This is a text node
            xml_parent_element.text = child_text
        else:
            # This is an element node
            child_element = ET.SubElement(xml_parent_element, child_tag)
            sync_treeview_to_xml(child_id, child_element)

def save_file():
    try:
        root_element = xml_tree.getroot()
        root_element.clear()
        sync_treeview_to_xml("", root_element)

        save_path = filedialog.asksaveasfilename(defaultextension=".xml",
                                                 filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
        if save_path:
            xml_tree.write(save_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            messagebox.showinfo("Success", f"File saved successfully to {save_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error saving file: {e}")

def on_tree_select(event):
    selected_items = treeview.selection()
    if selected_items:
        selected_item = selected_items[0]
        if 'text' in treeview.item(selected_item, 'tags'):
            start_pos, end_pos = text_positions.get(selected_item, ('1.0', '1.0'))
            text_output.tag_remove('sel', '1.0', tk.END)
            text_output.tag_add('sel', start_pos, end_pos)
            text_output.see(start_pos)

# Set up the main window
root = tk.Tk()
root.title("XML Tree Editor")

# Create a paned window
paned_window = PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

# Create a treeview in the left pane
treeview = ttk.Treeview(paned_window)
treeview.bind('<<TreeviewSelect>>', on_tree_select)
paned_window.add(treeview, width=200)

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
delete_button = tk.Button(button_frame, text="Delete Element", command=delete_selected_element)
delete_button.pack(side=tk.LEFT)
save_button = tk.Button(button_frame, text="Save XML File", command=save_file)
save_button.pack(side=tk.RIGHT)

root.mainloop()


