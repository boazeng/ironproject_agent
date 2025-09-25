#!/usr/bin/env python3
"""
Shape Positioning Tool
======================
A standalone tool for positioning input fields and labels over shape images.
This tool helps design the layout for shape popup modals.

Usage: python shape_positioning_tool.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
import os
from shape_template_generator import ShapeTemplateGenerator

class ShapePositioningTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Shape Positioning Tool - IRONMAN")
        self.root.geometry("1200x800")

        # Configure window behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(True, True)

        # Configure window to stay open
        self.root.attributes('-topmost', False)  # Don't always stay on top
        self.running = True

        # Data storage
        self.image_path = None
        self.image_original = None
        self.image_display = None
        self.canvas_image_id = None
        self.elements = []  # List of positioned elements
        self.selected_element = None
        self.drag_data = {"x": 0, "y": 0}

        # Default styling options
        self.default_font_size = 30
        self.default_font_color = "red"

        # Eraser tool state
        self.eraser_mode = False
        self.eraser_start_x = None
        self.eraser_start_y = None
        self.eraser_rect_id = None

        # Area definition mode
        self.area_mode = False
        self.area_type = "shape"  # "shape", "field", "label"
        self.area_start_x = None
        self.area_start_y = None
        self.area_rect_id = None
        self.defined_areas = {}

        # Absolute positioning system
        self.reference_point = None  # (x, y) coordinates of the absolute reference point
        self.reference_point_id = None  # Canvas ID of the reference point marker
        self.set_reference_mode = False  # Flag for setting reference point mode
        self.show_distances = True  # Show distance measurements

        # Shape configurations
        self.shape_configs = {
            '000': {'name': 'קו ישר', 'fields': ['A']},
            '104': {'name': 'צורת L', 'fields': ['A', 'C']},
            '107': {'name': 'צורת U', 'fields': ['A', 'C', 'E']},
            '218': {'name': 'צורה 218', 'fields': ['A', 'B', 'C']}
        }

        # Read shape from user configuration file
        self.current_shape = self.get_user_chosen_shape()

        # Initialize template generator
        self.template_generator = ShapeTemplateGenerator()

        self.setup_ui()
        # Delay loading to ensure UI is ready
        self.root.after(500, self.load_default_image)

    def get_user_chosen_shape(self):
        """Read the user chosen shape from the JSON file"""
        import json
        import os

        json_path = os.path.join('templates', 'shapes', 'user_choose_shape.json')

        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    shape = data.get('user_chosen_shape', '107')
                    print(f"Loading shape {shape} from user configuration")
                    return shape
        except Exception as e:
            print(f"Error reading user configuration: {e}")

        # Default fallback
        return '107'

    def setup_ui(self):
        """Setup the user interface"""

        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls with scrolling (compressed width)
        left_frame_outer = ttk.Frame(main_frame, width=200)
        left_frame_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame_outer.pack_propagate(False)

        # Create canvas and scrollbar for left panel
        left_canvas = tk.Canvas(left_frame_outer, width=180)
        left_scrollbar = ttk.Scrollbar(left_frame_outer, orient="vertical", command=left_canvas.yview)
        left_panel = ttk.Frame(left_canvas)

        # Configure canvas
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create window in canvas
        canvas_frame_id = left_canvas.create_window((0, 0), window=left_panel, anchor="nw")

        # Function to update scroll region
        def configure_scroll_region(event=None):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        # Function to adjust canvas width
        def configure_canvas_width(event=None):
            canvas_width = left_canvas.winfo_width()
            left_canvas.itemconfig(canvas_frame_id, width=canvas_width)

        # Bind events
        left_panel.bind('<Configure>', configure_scroll_region)
        left_canvas.bind('<Configure>', configure_canvas_width)

        # Enable mousewheel scrolling
        def on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        left_canvas.bind("<MouseWheel>", on_mousewheel)

        # Shape selection
        ttk.Label(left_panel, text="Shape:").pack(anchor=tk.W, pady=(0, 5))
        self.shape_var = tk.StringVar(value=self.current_shape)
        shape_combo = ttk.Combobox(left_panel, textvariable=self.shape_var,
                                  values=list(self.shape_configs.keys()), state="readonly")
        shape_combo.pack(fill=tk.X, pady=(0, 10))
        shape_combo.bind('<<ComboboxSelected>>', self.on_shape_changed)

        # Image controls
        ttk.Label(left_panel, text="Image:").pack(anchor=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Load Image", command=self.load_image).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Reset to Default", command=self.load_default_image).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Center Image", command=self.center_image).pack(fill=tk.X, pady=(0, 10))

        # Element controls
        ttk.Label(left_panel, text="Add Elements:").pack(anchor=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Add Label", command=self.add_label).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Add Input Field", command=self.add_input).pack(fill=tk.X, pady=(0, 10))

        # Eraser tool
        ttk.Label(left_panel, text="Image Editing:").pack(anchor=tk.W, pady=(0, 5))
        self.eraser_button = ttk.Button(left_panel, text="Enable Eraser", command=self.toggle_eraser)
        self.eraser_button.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Save Edited Image", command=self.save_edited_image).pack(fill=tk.X, pady=(0, 10))

        # Area definition tool
        ttk.Label(left_panel, text="Area Definition:").pack(anchor=tk.W, pady=(0, 5))

        # Area type selection
        area_type_frame = ttk.Frame(left_panel)
        area_type_frame.pack(fill=tk.X, pady=(0, 5))
        self.area_type_var = tk.StringVar(value="shape")
        ttk.Radiobutton(area_type_frame, text="Shape Area", variable=self.area_type_var, value="shape").pack(side=tk.LEFT)
        ttk.Radiobutton(area_type_frame, text="Field Area", variable=self.area_type_var, value="field").pack(side=tk.LEFT)
        ttk.Radiobutton(area_type_frame, text="Label Area", variable=self.area_type_var, value="label").pack(side=tk.LEFT)

        self.area_button = ttk.Button(left_panel, text="Define Area", command=self.toggle_area_mode)
        self.area_button.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Clear All Areas", command=self.clear_areas).pack(fill=tk.X, pady=(0, 10))

        # Absolute positioning controls
        ttk.Label(left_panel, text="Absolute Positioning:").pack(anchor=tk.W, pady=(0, 5))

        # Reference point controls
        ref_frame = ttk.Frame(left_panel)
        ref_frame.pack(fill=tk.X, pady=(0, 5))
        self.ref_button = ttk.Button(ref_frame, text="Set Reference Point", command=self.toggle_reference_mode)
        self.ref_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(ref_frame, text="Clear", command=self.clear_reference_point, width=8).pack(side=tk.LEFT)

        # Reference point coordinates display
        self.ref_coords_var = tk.StringVar(value="No reference point set")
        ttk.Label(left_panel, textvariable=self.ref_coords_var, font=("Arial", 8)).pack(anchor=tk.W, pady=(0, 5))

        # Current position display
        self.current_pos_var = tk.StringVar(value="Current position: Not set")
        ttk.Label(left_panel, textvariable=self.current_pos_var, font=("Arial", 8, "bold"), foreground="blue").pack(anchor=tk.W, pady=(0, 5))

        # Distance display toggle
        distance_frame = ttk.Frame(left_panel)
        distance_frame.pack(fill=tk.X, pady=(0, 10))
        self.show_distances_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(distance_frame, text="Show Distances", variable=self.show_distances_var,
                       command=self.toggle_distance_display).pack(side=tk.LEFT)

        # Current elements list
        ttk.Label(left_panel, text="Elements:").pack(anchor=tk.W, pady=(0, 5))

        # Elements listbox with scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.elements_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.elements_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.elements_listbox.yview)

        self.elements_listbox.bind('<<ListboxSelect>>', self.on_element_selected)

        # Catalog image preview button
        ttk.Button(left_panel, text="Preview Catalog Image", command=self.preview_catalog_image).pack(fill=tk.X, pady=(5, 10))

        # Element properties
        ttk.Label(left_panel, text="Properties:").pack(anchor=tk.W, pady=(0, 5))

        # Text property
        ttk.Label(left_panel, text="Text:").pack(anchor=tk.W)
        self.text_var = tk.StringVar()
        self.text_entry = ttk.Entry(left_panel, textvariable=self.text_var)
        self.text_entry.pack(fill=tk.X, pady=(0, 5))
        self.text_var.trace('w', self.on_text_changed)

        # Font size property
        ttk.Label(left_panel, text="Font Size:").pack(anchor=tk.W)
        self.font_size_var = tk.StringVar(value=str(self.default_font_size))
        font_size_frame = ttk.Frame(left_panel)
        font_size_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Entry(font_size_frame, textvariable=self.font_size_var, width=5).pack(side=tk.LEFT)
        ttk.Button(font_size_frame, text="Apply", command=self.on_font_size_changed, width=6).pack(side=tk.LEFT, padx=(2, 0))

        # Font color property
        ttk.Label(left_panel, text="Font Color:").pack(anchor=tk.W)
        color_frame = ttk.Frame(left_panel)
        color_frame.pack(fill=tk.X, pady=(0, 5))
        self.font_color_var = tk.StringVar(value=self.default_font_color)
        color_combo = ttk.Combobox(color_frame, textvariable=self.font_color_var, width=8,
                                  values=["red", "black", "blue", "green", "orange", "purple", "brown"])
        color_combo.pack(side=tk.LEFT)
        ttk.Button(color_frame, text="Apply", command=self.on_font_color_changed).pack(side=tk.LEFT, padx=(5, 0))

        # Delete button
        ttk.Button(left_panel, text="Delete Element", command=self.delete_element).pack(fill=tk.X, pady=(0, 10))

        # Export/Import
        ttk.Label(left_panel, text="Data:").pack(anchor=tk.W, pady=(0, 5))
        ttk.Button(left_panel, text="Export Layout", command=self.export_layout).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Import Layout", command=self.import_layout).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Generate HTML", command=self.generate_html).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left_panel, text="Export as Popup Template", command=self.export_popup_template).pack(fill=tk.X, pady=(0, 10))

        # Right panel - Canvas
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='white', scrollregion=(0, 0, 800, 600))

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Canvas bindings
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def load_default_image(self):
        """Load the default shape image"""
        shape_num = self.shape_var.get()
        default_path = f"C:\\Users\\User\\Aiprojects\\Iron-Projects\\Agents\\io\\catalog\\shape {shape_num}.png"

        if os.path.exists(default_path):
            self.load_image_file(default_path)
        else:
            messagebox.showwarning("Warning", f"Default image not found: {default_path}")

    def load_image(self):
        """Load an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Shape Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )

        if file_path:
            self.load_image_file(file_path)

    def load_image_file(self, file_path):
        """Load and display an image file"""
        try:
            self.image_path = file_path
            self.image_original = Image.open(file_path)

            # Resize image if too large
            max_size = (600, 400)
            self.image_original.thumbnail(max_size, Image.Resampling.LANCZOS)

            self.image_display = ImageTk.PhotoImage(self.image_original)

            # Clear canvas and add image centered
            self.canvas.delete("all")

            # Force canvas to update and get actual dimensions
            self.canvas.update_idletasks()

            # Calculate center position with fallback values
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Use larger default values if canvas isn't properly sized yet
            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 600

            center_x = canvas_width // 2
            center_y = canvas_height // 2

            self.canvas_image_id = self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.image_display)

            # Update canvas scroll region
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)

            # Clear elements
            self.elements = []
            self.update_elements_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def on_shape_changed(self, event=None):
        """Handle shape selection change"""
        self.current_shape = self.shape_var.get()
        self.load_default_image()

    def center_image(self):
        """Center the current image on the canvas"""
        if self.canvas_image_id and self.image_display:
            # Force canvas update
            self.canvas.update_idletasks()

            # Get actual canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate center
            center_x = canvas_width // 2
            center_y = canvas_height // 2

            # Move image to center
            self.canvas.coords(self.canvas_image_id, center_x, center_y)

            # Update scroll region
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)

    def preview_catalog_image(self):
        """Preview the current shape's catalog image in a popup window"""
        if not self.image_path:
            messagebox.showwarning("Warning", "No image loaded to preview")
            return

        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Catalog Image Preview - Shape {self.current_shape}")
        preview_window.geometry("500x400")
        preview_window.resizable(True, True)

        # Center the window on screen
        preview_window.transient(self.root)
        preview_window.grab_set()

        # Create main frame
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title label
        title_label = ttk.Label(main_frame, text=f"Shape {self.current_shape} - Catalog Image",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Image display frame
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)

        try:
            # Load and resize image for preview
            preview_image = Image.open(self.image_path)

            # Calculate size to fit in preview window
            max_width = 450
            max_height = 300

            # Calculate aspect ratio
            img_width, img_height = preview_image.size
            ratio = min(max_width/img_width, max_height/img_height)

            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)

            preview_image = preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            preview_photo = ImageTk.PhotoImage(preview_image)

            # Create label to display image
            image_label = ttk.Label(image_frame, image=preview_photo)
            image_label.pack(expand=True)

            # Keep reference to prevent garbage collection
            image_label.image = preview_photo

            # Image info
            info_label = ttk.Label(main_frame,
                                 text=f"Original size: {img_width}x{img_height} | File: {os.path.basename(self.image_path)}")
            info_label.pack(pady=(10, 0))

        except Exception as e:
            error_label = ttk.Label(image_frame, text=f"Error loading image: {str(e)}")
            error_label.pack(expand=True)

        # Close button
        close_button = ttk.Button(main_frame, text="Close",
                                command=preview_window.destroy)
        close_button.pack(pady=(10, 0))

    def add_label(self):
        """Add a label element"""
        if not self.image_display:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        # Get shape config for default labels
        config = self.shape_configs.get(self.current_shape, {})
        fields = config.get('fields', ['A'])

        # Use next available field letter
        existing_labels = [e['text'] for e in self.elements if e['type'] == 'label']
        for field in fields:
            if field not in existing_labels:
                text = field
                break
        else:
            text = f"Label{len(self.elements)+1}"

        element = {
            'type': 'label',
            'text': text,
            'x': 100,
            'y': 100,
            'canvas_id': None
        }

        self.elements.append(element)
        self.draw_element(element)
        self.update_elements_list()

        # Update current position display to show absolute coordinates
        self.update_current_position_display(element['x'], element['y'])

    def add_input(self):
        """Add an input field element"""
        if not self.image_display:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        element = {
            'type': 'input',
            'text': 'Input Field',
            'x': 150,
            'y': 150,
            'canvas_id': None
        }

        self.elements.append(element)
        self.draw_element(element)
        self.update_elements_list()

        # Update current position display to show absolute coordinates
        self.update_current_position_display(element['x'], element['y'])

    def draw_element(self, element):
        """Draw an element on the canvas"""
        x, y = element['x'], element['y']

        # Get font properties from element or use defaults
        font_size = element.get('font_size', self.default_font_size)
        font_color = element.get('font_color', self.default_font_color)

        if element['type'] == 'label':
            # Draw label as text
            element['canvas_id'] = self.canvas.create_text(
                x, y, text=element['text'], font=("Arial", font_size, "bold"),
                fill=font_color, anchor=tk.CENTER, tags="draggable"
            )
        elif element['type'] == 'input':
            # Draw input as rectangle with text
            element['canvas_id'] = self.canvas.create_rectangle(
                x-40, y-15, x+40, y+15, fill="lightblue", outline="blue",
                tags="draggable"
            )
            # Add text inside rectangle
            text_id = self.canvas.create_text(
                x, y, text=element['text'], font=("Arial", 10),
                fill="black", tags="draggable"
            )
            element['text_id'] = text_id

    def update_elements_list(self):
        """Update the elements listbox"""
        self.elements_listbox.delete(0, tk.END)
        for i, element in enumerate(self.elements):
            self.elements_listbox.insert(tk.END, f"{element['type']}: {element['text']}")

    def update_current_position_display(self, x, y):
        """Update the current position display with absolute coordinates"""
        if self.reference_point:
            # Calculate absolute position relative to reference point
            rel_x = x - self.reference_point[0]
            rel_y = y - self.reference_point[1]
            distance = ((rel_x ** 2) + (rel_y ** 2)) ** 0.5
            self.current_pos_var.set(f"Position: ({x},{y}) | Absolute: ({rel_x:+.0f},{rel_y:+.0f}) | Distance: {distance:.1f}")
        else:
            self.current_pos_var.set(f"Position: ({x},{y}) | Set reference point for absolute coordinates")

    def on_element_selected(self, event=None):
        """Handle element selection from listbox"""
        selection = self.elements_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.elements):
                self.selected_element = self.elements[index]
                self.text_var.set(self.selected_element['text'])

                # Load font properties
                font_size = self.selected_element.get('font_size', self.default_font_size)
                font_color = self.selected_element.get('font_color', self.default_font_color)
                self.font_size_var.set(str(font_size))
                self.font_color_var.set(font_color)

                # Update position display to show absolute coordinates of selected element
                self.update_current_position_display(self.selected_element['x'], self.selected_element['y'])

    def on_text_changed(self, *args):
        """Handle text property change"""
        if self.selected_element:
            new_text = self.text_var.get()
            self.selected_element['text'] = new_text

            # Update display
            if self.selected_element['type'] == 'label':
                self.canvas.itemconfig(self.selected_element['canvas_id'], text=new_text)
            elif self.selected_element['type'] == 'input':
                if 'text_id' in self.selected_element:
                    self.canvas.itemconfig(self.selected_element['text_id'], text=new_text)

            self.update_elements_list()

    def delete_element(self):
        """Delete the selected element"""
        if self.selected_element:
            # Remove from canvas
            if self.selected_element['canvas_id']:
                self.canvas.delete(self.selected_element['canvas_id'])
            if 'text_id' in self.selected_element:
                self.canvas.delete(self.selected_element['text_id'])

            # Remove from list
            self.elements.remove(self.selected_element)
            self.selected_element = None
            self.text_var.set("")
            self.update_elements_list()

    def on_canvas_click(self, event):
        """Handle canvas click"""
        if self.set_reference_mode:
            # Set reference point
            self.set_reference_point(event.x, event.y)
            return

        if self.eraser_mode:
            # Start eraser selection
            self.eraser_start_x = event.x
            self.eraser_start_y = event.y
            return

        if self.area_mode:
            # Start area selection
            self.area_start_x = event.x
            self.area_start_y = event.y
            return

        # Find clicked item
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]

        # Check if it's a draggable element
        if "draggable" in self.canvas.gettags(clicked_item):
            # Find corresponding element
            for element in self.elements:
                if (element['canvas_id'] == clicked_item or
                    element.get('text_id') == clicked_item):
                    self.selected_element = element
                    self.text_var.set(element['text'])
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
                    break

    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.eraser_mode:
            # Update eraser rectangle
            if self.eraser_start_x is not None and self.eraser_start_y is not None:
                if self.eraser_rect_id:
                    self.canvas.delete(self.eraser_rect_id)

                self.eraser_rect_id = self.canvas.create_rectangle(
                    self.eraser_start_x, self.eraser_start_y, event.x, event.y,
                    outline="red", width=2, fill="", tags="eraser_rect"
                )
            return

        if self.area_mode:
            # Update area rectangle
            if self.area_start_x is not None and self.area_start_y is not None:
                if self.area_rect_id:
                    self.canvas.delete(self.area_rect_id)

                area_type = self.area_type_var.get()
                color = {"shape": "blue", "field": "green", "label": "orange"}.get(area_type, "blue")

                self.area_rect_id = self.canvas.create_rectangle(
                    self.area_start_x, self.area_start_y, event.x, event.y,
                    outline=color, width=3, fill="", tags=f"area_rect_{area_type}"
                )
            return

        if self.selected_element:
            # Calculate movement
            delta_x = event.x - self.drag_data["x"]
            delta_y = event.y - self.drag_data["y"]

            # Move the element
            self.canvas.move(self.selected_element['canvas_id'], delta_x, delta_y)
            if 'text_id' in self.selected_element:
                self.canvas.move(self.selected_element['text_id'], delta_x, delta_y)

            # Update position
            self.selected_element['x'] += delta_x
            self.selected_element['y'] += delta_y

            # Update drag data
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

            # Update current position display with absolute coordinates
            self.update_current_position_display(self.selected_element['x'], self.selected_element['y'])

            # Update distance displays if reference point is set
            if self.reference_point and self.show_distances:
                self.update_distance_displays()

    def on_canvas_release(self, event):
        """Handle canvas release"""
        if self.eraser_mode:
            # Apply eraser
            if self.eraser_start_x is not None and self.eraser_start_y is not None:
                self.apply_eraser(self.eraser_start_x, self.eraser_start_y, event.x, event.y)

                # Clean up eraser rectangle
                if self.eraser_rect_id:
                    self.canvas.delete(self.eraser_rect_id)
                    self.eraser_rect_id = None

                self.eraser_start_x = None
                self.eraser_start_y = None
            return

        if self.area_mode:
            # Save defined area
            if self.area_start_x is not None and self.area_start_y is not None:
                area_type = self.area_type_var.get()

                # Calculate area bounds
                x1, x2 = min(self.area_start_x, event.x), max(self.area_start_x, event.x)
                y1, y2 = min(self.area_start_y, event.y), max(self.area_start_y, event.y)

                # Store the defined area
                self.defined_areas[area_type] = {
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'width': x2 - x1, 'height': y2 - y1
                }

                # Convert the temporary rectangle to a permanent one
                if self.area_rect_id:
                    self.canvas.delete(self.area_rect_id)

                area_type = self.area_type_var.get()
                color = {"shape": "blue", "field": "green", "label": "orange"}.get(area_type, "blue")

                # Create permanent area boundary
                permanent_rect_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=color, width=2, fill="", tags="area_boundary",
                    dash=(5, 5)  # Dashed line for permanent boundaries
                )

                # Add text label
                center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_text(
                    center_x, center_y, text=f"{area_type.upper()} AREA",
                    fill=color, font=("Arial", 10, "bold"), tags="area_boundary"
                )

                messagebox.showinfo("Area Defined",
                                   f"{area_type.capitalize()} area defined: {int(x2-x1)}×{int(y2-y1)} pixels")

                # Reset area selection
                self.area_rect_id = None
                self.area_start_x = None
                self.area_start_y = None
            return

        # Reset drag data
        self.drag_data = {"x": 0, "y": 0}

    def export_layout(self):
        """Export the current layout to JSON and automatically generate HTML template"""
        if not self.elements:
            messagebox.showwarning("Warning", "No elements to export")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Layout",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                # Enhanced data structure for the template generator
                data = {
                    'shape_number': self.current_shape,
                    'shape_name': self.shape_configs.get(self.current_shape, {}).get('name', f'Shape {self.current_shape}'),
                    'image_path': self.image_path,
                    'canvas_width': 350,
                    'canvas_height': 250,
                    'elements': []
                }

                # Add absolute positioning information if reference point is set
                if self.reference_point:
                    data['absolute_positioning'] = {
                        'reference_point': {'x': self.reference_point[0], 'y': self.reference_point[1]},
                        'enabled': True
                    }
                else:
                    data['absolute_positioning'] = {
                        'enabled': False
                    }

                # Process elements for template generation
                for e in self.elements:
                    element_data = {
                        'type': e['type'],
                        'text': e.get('text', ''),
                        'x': e['x'],
                        'y': e['y']
                    }

                    # Add absolute positioning data if reference point is set
                    if self.reference_point:
                        ref_x, ref_y = self.reference_point
                        element_data['absolute_positioning'] = {
                            'relative_x': e['x'] - ref_x,
                            'relative_y': e['y'] - ref_y,
                            'distance_from_ref': ((e['x'] - ref_x)**2 + (e['y'] - ref_y)**2)**0.5
                        }

                    # Add additional properties based on element type
                    if e['type'] == 'text':
                        element_data['font_size'] = e.get('font_size', self.default_font_size)
                        element_data['color'] = e.get('color', self.default_font_color)
                    elif e['type'] == 'line':
                        element_data['start_x'] = e.get('start_x', e['x'])
                        element_data['start_y'] = e.get('start_y', e['y'])
                        element_data['end_x'] = e.get('end_x', e['x'] + 50)
                        element_data['end_y'] = e.get('end_y', e['y'])
                        element_data['color'] = e.get('color', 'black')
                        element_data['width'] = e.get('width', 2)
                    elif e['type'] == 'rectangle':
                        element_data['width'] = e.get('width', 50)
                        element_data['height'] = e.get('height', 50)
                        element_data['color'] = e.get('color', 'black')
                        element_data['line_width'] = e.get('line_width', 2)

                    data['elements'].append(element_data)

                # Save JSON file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Auto-generate HTML template
                try:
                    html_file_path = self.template_generator.json_to_html(file_path, self.current_shape)
                    success_message = f"Layout exported to {file_path}\n\nHTML template automatically generated: {html_file_path}"
                    messagebox.showinfo("Success", success_message)
                except Exception as template_error:
                    warning_message = f"Layout exported to {file_path}\n\nWarning: Could not generate HTML template: {str(template_error)}"
                    messagebox.showwarning("Partial Success", warning_message)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def import_layout(self):
        """Import a layout from JSON"""
        file_path = filedialog.askopenfilename(
            title="Import Layout",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Load shape and image
                if 'shape' in data:
                    self.shape_var.set(data['shape'])
                    self.current_shape = data['shape']

                if 'image_path' in data and os.path.exists(data['image_path']):
                    self.load_image_file(data['image_path'])

                # Clear existing elements
                self.canvas.delete("draggable")
                self.elements = []

                # Load elements
                for elem_data in data.get('elements', []):
                    element = {
                        'type': elem_data['type'],
                        'text': elem_data['text'],
                        'x': elem_data['x'],
                        'y': elem_data['y'],
                        'canvas_id': None
                    }
                    self.elements.append(element)
                    self.draw_element(element)

                self.update_elements_list()
                messagebox.showinfo("Success", "Layout imported successfully")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")

    def generate_html(self):
        """Generate HTML template code"""
        if not self.elements:
            messagebox.showwarning("Warning", "No elements to generate")
            return

        # Calculate relative positions (assuming 400x200 SVG viewport)
        if not self.image_original:
            messagebox.showwarning("Warning", "No image loaded")
            return

        img_width, img_height = self.image_original.size

        html_parts = []
        html_parts.append(f"<!-- Generated layout for shape {self.current_shape} -->")
        html_parts.append('<div class="shape-diagram-with-input" style="position: relative; text-align: center; padding: 40px 0;">')

        # Group elements by field letter for inputs
        labels = [e for e in self.elements if e['type'] == 'label']
        inputs = [e for e in self.elements if e['type'] == 'input']

        # Generate input field HTML
        for i, label in enumerate(labels):
            field_letter = label['text']

            # Calculate percentage positions
            left_percent = (label['x'] / img_width) * 100
            top_percent = (label['y'] / img_height) * 100

            html_parts.append(f'    <div style="position: absolute; top: {top_percent:.1f}%; left: {left_percent:.1f}%; transform: translate(-50%, -50%); display: flex; align-items: center;">')
            html_parts.append(f'        <input type="text"')
            html_parts.append(f'               id="length-{field_letter}-{self.current_shape}"')
            html_parts.append(f'               class="inline-shape-input shape-{self.current_shape}-input"')
            html_parts.append(f'               maxlength="8"')
            html_parts.append(f'               placeholder="0"')
            html_parts.append(f'               style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #333; border-radius: 4px; margin-right: 4px;">')
            html_parts.append(f'        <span style="font-size: 20px; font-weight: bold; margin-left: 4px;">= {field_letter}</span>')
            html_parts.append(f'    </div>')

        # Add image
        html_parts.append(f'    <div style="text-align: center; margin-top: 20px;">')
        html_parts.append(f'        <img src="/static/images/shape_{self.current_shape}.png"')
        html_parts.append(f'             alt="Shape {self.current_shape}"')
        html_parts.append(f'             style="max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;">')
        html_parts.append(f'    </div>')

        html_parts.append('</div>')

        # Show in a new window
        html_code = '\n'.join(html_parts)
        self.show_generated_code(html_code)

    def show_generated_code(self, code):
        """Show generated code in a new window"""
        code_window = tk.Toplevel(self.root)
        code_window.title("Generated HTML Code")
        code_window.geometry("800x600")

        # Text widget with scrollbar
        frame = ttk.Frame(code_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(frame, wrap=tk.NONE, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert('1.0', code)
        text_widget.config(state=tk.DISABLED)

        # Copy button
        def copy_code():
            code_window.clipboard_clear()
            code_window.clipboard_append(code)
            messagebox.showinfo("Copied", "Code copied to clipboard")

        ttk.Button(code_window, text="Copy to Clipboard", command=copy_code).pack(pady=10)

    def on_font_size_changed(self):
        """Handle font size change"""
        if self.selected_element and self.selected_element['type'] == 'label':
            try:
                new_size = int(self.font_size_var.get())
                if new_size > 0:
                    self.selected_element['font_size'] = new_size

                    # Update display
                    font_color = self.selected_element.get('font_color', self.default_font_color)
                    self.canvas.itemconfig(self.selected_element['canvas_id'],
                                         font=("Arial", new_size, "bold"))
            except ValueError:
                messagebox.showwarning("Warning", "Please enter a valid font size number")

    def on_font_color_changed(self):
        """Handle font color change"""
        if self.selected_element and self.selected_element['type'] == 'label':
            new_color = self.font_color_var.get()
            self.selected_element['font_color'] = new_color

            # Update display
            self.canvas.itemconfig(self.selected_element['canvas_id'], fill=new_color)

    def toggle_eraser(self):
        """Toggle eraser mode on/off"""
        self.eraser_mode = not self.eraser_mode

        if self.eraser_mode:
            self.eraser_button.configure(text="Disable Eraser", style="Accent.TButton")
            self.canvas.configure(cursor="crosshair")
            messagebox.showinfo("Eraser Mode", "Click and drag to select areas to erase from the image.\n\nThe selected area will be filled with white to remove original letters.")
        else:
            self.eraser_button.configure(text="Enable Eraser", style="TButton")
            self.canvas.configure(cursor="")

            # Clean up any eraser rectangle
            if self.eraser_rect_id:
                self.canvas.delete(self.eraser_rect_id)
                self.eraser_rect_id = None

    def toggle_area_mode(self):
        """Toggle area definition mode on/off"""
        self.area_mode = not self.area_mode

        if self.area_mode:
            # Disable eraser mode if active
            if self.eraser_mode:
                self.toggle_eraser()

            area_type = self.area_type_var.get()
            self.area_button.configure(text=f"Exit Area Mode", style="Accent.TButton")
            self.canvas.configure(cursor="crosshair")
            messagebox.showinfo("Area Definition Mode",
                               f"Click and drag to define the {area_type} area.\n\n"
                               f"This will help position elements accurately within the defined boundary.")
        else:
            self.area_button.configure(text="Define Area", style="TButton")
            self.canvas.configure(cursor="")

            # Clean up any area rectangle
            if self.area_rect_id:
                self.canvas.delete(self.area_rect_id)
                self.area_rect_id = None

    def clear_areas(self):
        """Clear all defined areas"""
        self.defined_areas.clear()

        # Remove any visual indicators from canvas
        for item_id in list(self.canvas.find_all()):
            tags = self.canvas.gettags(item_id)
            if 'area_boundary' in tags:
                self.canvas.delete(item_id)

        messagebox.showinfo("Areas Cleared", "All defined areas have been cleared.")

    def apply_eraser(self, x1, y1, x2, y2):
        """Apply eraser to the selected rectangular area"""
        if not self.image_original or not self.canvas_image_id:
            return

        try:
            # Get image position on canvas
            canvas_coords = self.canvas.coords(self.canvas_image_id)
            if len(canvas_coords) != 2:
                return

            img_center_x, img_center_y = canvas_coords
            img_width = self.image_original.width
            img_height = self.image_original.height

            # Calculate image boundaries on canvas
            img_left = img_center_x - img_width // 2
            img_top = img_center_y - img_height // 2
            img_right = img_left + img_width
            img_bottom = img_top + img_height

            # Convert canvas coordinates to image coordinates
            # Ensure coordinates are within image bounds
            img_x1 = max(0, min(img_width, int(x1 - img_left)))
            img_y1 = max(0, min(img_height, int(y1 - img_top)))
            img_x2 = max(0, min(img_width, int(x2 - img_left)))
            img_y2 = max(0, min(img_height, int(y2 - img_top)))

            # Ensure we have a valid rectangle
            if img_x1 == img_x2 or img_y1 == img_y2:
                return

            # Ensure x1,y1 is top-left and x2,y2 is bottom-right
            if img_x1 > img_x2:
                img_x1, img_x2 = img_x2, img_x1
            if img_y1 > img_y2:
                img_y1, img_y2 = img_y2, img_y1

            # Create a copy of the image and erase the selected area
            img_copy = self.image_original.copy()
            draw = ImageDraw.Draw(img_copy)

            # Fill the rectangle with white
            draw.rectangle([img_x1, img_y1, img_x2, img_y2], fill="white")

            # Update the displayed image
            self.image_original = img_copy
            self.image_display = ImageTk.PhotoImage(img_copy)
            self.canvas.itemconfig(self.canvas_image_id, image=self.image_display)

            print(f"Erased area: ({img_x1},{img_y1}) to ({img_x2},{img_y2})")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply eraser: {str(e)}")

    def save_edited_image(self):
        """Save the edited image to catalog_clean folder"""
        if not self.image_original:
            messagebox.showwarning("Warning", "No image to save")
            return

        try:
            # Auto-generate file path
            clean_folder = "C:\\Users\\User\\Aiprojects\\Iron-Projects\\Agents\\io\\catalog\\catalog_clean"
            shape_num = self.current_shape
            filename = f"shape_{shape_num}_clean.png"
            file_path = os.path.join(clean_folder, filename)

            # Create directory if it doesn't exist
            os.makedirs(clean_folder, exist_ok=True)

            # Save the image
            self.image_original.save(file_path)

            # Also save to static/images for web display
            static_path = f"C:\\Users\\User\\Aiprojects\\Iron-Projects\\Agents\\static\\images\\shape_{shape_num}.png"
            static_dir = os.path.dirname(static_path)
            os.makedirs(static_dir, exist_ok=True)
            self.image_original.save(static_path)

            messagebox.showinfo("Success",
                f"Cleaned image saved to:\n"
                f"• {file_path}\n"
                f"• {static_path}\n\n"
                f"The cleaned image is now ready for use in your popup!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def export_popup_template(self):
        """Export complete popup template for integration into main system"""
        if not self.elements:
            messagebox.showwarning("Warning", "No elements to export")
            return

        # Get all field elements (both labels and input fields)
        labels = [e for e in self.elements if e['type'] in ['label', 'input']]

        if not labels:
            messagebox.showwarning("Warning", "No input fields found. Add input fields first.")
            return

        # Ask user for export options
        export_options = self.show_export_options_dialog()
        if not export_options:
            return

        export_type = export_options['type']

        if export_type == 'replace':
            self.replace_in_main_file(labels)
        elif export_type == 'save_template':
            self.save_as_template_file(labels)
        elif export_type == 'copy_clipboard':
            self.copy_template_to_clipboard(labels)

    def show_export_options_dialog(self):
        """Show dialog for export options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Popup Template")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        result = {'type': None}

        ttk.Label(dialog, text="Choose how to export your popup template:", font=("Arial", 12)).pack(pady=10)

        # Option 1: Replace in main file
        ttk.Button(dialog, text=f"1. Replace Shape {self.current_shape} in Main System",
                  command=lambda: self.set_export_type(result, dialog, 'replace')).pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dialog, text="   • Saves to templates/shapes/ directory (automatically loaded)",
                 foreground="gray").pack(anchor=tk.W, padx=40)

        # Option 2: Save as template file
        ttk.Button(dialog, text="2. Save as Template File",
                  command=lambda: self.set_export_type(result, dialog, 'save_template')).pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dialog, text="   • Saves complete template code to a file",
                 foreground="gray").pack(anchor=tk.W, padx=40)

        # Option 3: Copy to clipboard
        ttk.Button(dialog, text="3. Copy Template Code to Clipboard",
                  command=lambda: self.set_export_type(result, dialog, 'copy_clipboard')).pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dialog, text="   • Copy code to paste manually",
                 foreground="gray").pack(anchor=tk.W, padx=40)

        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=20)

        # Wait for dialog to close
        dialog.wait_window()
        return result if result['type'] else None

    def set_export_type(self, result, dialog, export_type):
        """Set export type and close dialog"""
        result['type'] = export_type
        dialog.destroy()

    def replace_in_main_file(self, labels):
        """Save template to the templates/shapes/ directory (automatically loaded by web system)"""
        # Ensure templates/shapes directory exists
        templates_dir = os.path.join("templates", "shapes")
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)

        # Save to proper template file location
        template_file = os.path.join(templates_dir, f"shape_{self.current_shape}.html")

        try:
            # Generate the new template HTML (not JavaScript)
            template_html = self.generate_shape_template(labels)

            # Write template to proper location
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_html)

            messagebox.showinfo("Success", f"Shape {self.current_shape} template saved to {template_file}\n\nThe web system will automatically load this template when needed.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template file: {str(e)}")

    def save_as_template_file(self, labels):
        """Save template as a separate file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Popup Template",
            defaultextension=".js",
            filetypes=[("JavaScript files", "*.js"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                template = self.generate_shape_template(labels)
                full_template = f"// Shape {self.current_shape} Popup Template - Generated by Shape Positioning Tool\n\n'{self.current_shape}': `{template}`"

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_template)

                messagebox.showinfo("Success", f"Template saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template: {str(e)}")

    def copy_template_to_clipboard(self, labels):
        """Copy template code to clipboard"""
        try:
            template = self.generate_shape_template(labels)
            full_template = f"'{self.current_shape}': `{template}`"

            self.root.clipboard_clear()
            self.root.clipboard_append(full_template)
            messagebox.showinfo("Copied", f"Template code copied to clipboard!\n\nYou can now paste it to replace the shape {self.current_shape} template in your code.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")

    def generate_shape_template(self, labels):
        """Generate the complete shape template HTML"""
        if not self.image_original:
            raise Exception("No image loaded")

        shape_num = self.current_shape

        # Sort labels by field name for consistent output
        labels_sorted = sorted(labels, key=lambda x: x['text'])

        template_parts = []
        template_parts.append(f"")
        template_parts.append(f"        <div id=\"shape-{shape_num}\" class=\"shape-content\">")
        template_parts.append(f"            <div class=\"shape-diagram-with-input\" style=\"position: relative; text-align: center; padding: 40px 0;\">")

        # Generate input field positioning for each label
        for label in labels_sorted:
            field_letter = label['text']

            # Get image position on canvas
            canvas_coords = self.canvas.coords(self.canvas_image_id)
            if len(canvas_coords) == 2:
                img_center_x, img_center_y = canvas_coords
                img_width = self.image_original.width
                img_height = self.image_original.height

                # Calculate image boundaries on canvas
                img_left = img_center_x - img_width // 2
                img_top = img_center_y - img_height // 2

                # Convert label position to relative position within image
                relative_x = (label['x'] - img_left) / img_width
                relative_y = (label['y'] - img_top) / img_height

                # Clamp values to reasonable ranges (allow full range for precision)
                relative_x = max(0.0, min(1.0, relative_x))
                relative_y = max(0.0, min(1.0, relative_y))

                # Convert to percentages for web display accounting for actual template layout
                # The template has a container where inputs are positioned absolutely,
                # but the image appears below with margin-top: 20px
                # We need to map image coordinates to container coordinates

                # In the final template:
                # - Container has padding: 40px 0 (top/bottom padding)
                # - Image has margin-top: 20px and is max-width: 300px
                # - Input fields are positioned absolutely within the container

                # Calculate the effective image position within the container
                container_padding_top = 40  # padding from container style
                image_margin_top = 20       # margin-top from image style

                # The image effectively starts at this position in the container
                effective_image_top = container_padding_top + image_margin_top

                # Convert image-relative coordinates to container-relative percentages
                # Get actual image dimensions for proper scaling
                actual_img_width = self.image_original.width
                actual_img_height = self.image_original.height

                # Template displays image with max-width: 300px
                display_img_width = 300
                # Calculate display height maintaining aspect ratio
                display_img_height = (actual_img_height / actual_img_width) * display_img_width

                # Container dimensions (based on template structure)
                container_width = 400  # Approximate container width for horizontal centering
                # Container height = padding-top + image height + padding for inputs
                container_height = container_padding_top + image_margin_top + display_img_height + 40

                # Map the relative position on the image to the position in the container
                # The image is centered in the container (text-align: center)
                # Image is 300px wide in a wider container
                # We need to calculate where the image sits within the container
                # and then position relative to the image location

                # Since image is centered and 300px wide, calculate its position
                # The template uses text-align: center and the image has max-width: 300px
                # We need to be more conservative with the scaling
                # The actual container in the modal/page is wider than 400px
                # Let's use a more accurate scaling factor
                image_width_percent = 60  # More conservative estimate for 300px image in wider container
                image_left_offset = (100 - image_width_percent) / 2  # Center offset (20% on each side)
                web_left_percent = image_left_offset + (relative_x * image_width_percent)

                # Vertical: account for where image actually appears in the container
                web_top_percent = ((effective_image_top + relative_y * display_img_height) / container_height) * 100
            else:
                # Fallback positioning
                web_left_percent = 50
                web_top_percent = 50

            # Check if this is a standalone input field (created via "Add Input Field")
            is_standalone_input = field_letter == "Input Field"

            if is_standalone_input:
                # Create standalone input field without label
                template_parts.append(f"                <!-- Standalone input field -->")
                template_parts.append(f"                <div style=\"position: absolute; top: {web_top_percent:.1f}%; left: {web_left_percent:.1f}%; transform: translate(-50%, -50%);\">")
                template_parts.append(f"                    <input type=\"text\"")
                template_parts.append(f"                           id=\"length-field_{len([l for l in labels_sorted if l['text'] == 'Input Field' and labels_sorted.index(l) <= labels_sorted.index(label)])}-{shape_num}\"")
                template_parts.append(f"                           class=\"inline-shape-input shape-{shape_num}-input\"")
                template_parts.append(f"                           maxlength=\"8\"")
                template_parts.append(f"                           placeholder=\"0\"")
                template_parts.append(f"                           style=\"width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;\">")
                template_parts.append(f"                </div>")
            else:
                # Create labeled input field
                template_parts.append(f"                <!-- {field_letter} field with label -->")
                template_parts.append(f"                <div style=\"position: absolute; top: {web_top_percent:.1f}%; left: {web_left_percent:.1f}%; transform: translate(-50%, -50%); display: flex; align-items: center;\">")
                template_parts.append(f"                    <span style=\"font-size: 20px; font-weight: bold; color: red; margin-right: 8px;\">{field_letter}</span>")
                template_parts.append(f"                    <input type=\"text\"")
                template_parts.append(f"                           id=\"length-{field_letter}-{shape_num}\"")
                template_parts.append(f"                           class=\"inline-shape-input shape-{shape_num}-input\"")
                template_parts.append(f"                           maxlength=\"8\"")
                template_parts.append(f"                           placeholder=\"0\"")
                template_parts.append(f"                           style=\"width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;\">")
                template_parts.append(f"                </div>")

        # Add image after input fields (matches current template structure)
        template_parts.append(f"")
        template_parts.append(f"                <!-- Original catalog shape {shape_num} image -->")
        template_parts.append(f"                <div style=\"text-align: center; margin-top: 20px;\">")
        template_parts.append(f"                    <img src=\"/static/images/shape_{shape_num}.png?v=2024092403\"")
        template_parts.append(f"                         alt=\"Shape {shape_num}\"")
        template_parts.append(f"                         style=\"max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;\">")
        template_parts.append(f"                </div>")

        # Close the shape diagram container
        template_parts.append(f"            </div>")
        template_parts.append(f"            <div class=\"modal-buttons\" style=\"margin-top: 30px;\">")
        template_parts.append(f"                <button id=\"save-shape-{shape_num}\" class=\"btn btn-success\" onclick=\"saveShape('{shape_num}')\">שמור</button>")
        template_parts.append(f"            </div>")
        template_parts.append(f"        </div>")
        template_parts.append(f"    ")

        return '\n'.join(template_parts)

    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit the Shape Positioning Tool?\n\nAny unsaved changes will be lost."):
            self.running = False
            self.root.quit()
            self.root.destroy()

    # ========== ABSOLUTE POSITIONING METHODS ==========

    def toggle_reference_mode(self):
        """Toggle reference point setting mode"""
        self.set_reference_mode = not self.set_reference_mode
        if self.set_reference_mode:
            self.ref_button.config(text="Click to Set Reference")
            messagebox.showinfo("Reference Mode", "Click on the canvas to set the absolute reference point.")
        else:
            self.ref_button.config(text="Set Reference Point")

    def set_reference_point(self, x, y):
        """Set the absolute reference point"""
        # Remove previous reference point marker
        if self.reference_point_id:
            self.canvas.delete(self.reference_point_id)

        # Set the reference point
        self.reference_point = (x, y)

        # Create visual marker for reference point
        size = 10
        self.reference_point_id = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill="red", outline="darkred", width=3, tags="reference_point"
        )

        # Add crosshairs
        crosshair_size = 20
        self.canvas.create_line(x - crosshair_size, y, x + crosshair_size, y,
                               fill="red", width=2, tags="reference_point")
        self.canvas.create_line(x, y - crosshair_size, x, y + crosshair_size,
                               fill="red", width=2, tags="reference_point")

        # Update coordinate display
        self.ref_coords_var.set(f"Reference: ({x}, {y})")

        # Exit reference mode
        self.set_reference_mode = False
        self.ref_button.config(text="Set Reference Point")

        # Update distance displays for all elements
        self.update_distance_displays()

        messagebox.showinfo("Reference Set", f"Reference point set at ({x}, {y})")

    def clear_reference_point(self):
        """Clear the reference point"""
        if self.reference_point_id:
            self.canvas.delete("reference_point")
            self.reference_point_id = None
            self.reference_point = None
            self.ref_coords_var.set("No reference point set")

            # Clear distance displays
            self.canvas.delete("distance_line")
            self.canvas.delete("distance_text")

    def toggle_distance_display(self):
        """Toggle distance display on/off"""
        self.show_distances = self.show_distances_var.get()
        if self.show_distances:
            self.update_distance_displays()
        else:
            self.canvas.delete("distance_line")
            self.canvas.delete("distance_text")

    def update_distance_displays(self):
        """Update distance displays for all elements"""
        if not self.reference_point or not self.show_distances:
            return

        # Clear existing distance displays
        self.canvas.delete("distance_line")
        self.canvas.delete("distance_text")

        ref_x, ref_y = self.reference_point

        for element in self.elements:
            ex, ey = element['x'], element['y']

            # Calculate distance
            dx = ex - ref_x
            dy = ey - ref_y
            distance = (dx**2 + dy**2)**0.5

            # Draw line from reference point to element
            self.canvas.create_line(ref_x, ref_y, ex, ey,
                                   fill="lightblue", width=1, dash=(5, 5), tags="distance_line")

            # Display distance text
            mid_x, mid_y = (ref_x + ex) / 2, (ref_y + ey) / 2
            self.canvas.create_text(mid_x, mid_y,
                                   text=f"d={distance:.1f}\n({dx:+.0f}, {dy:+.0f})",
                                   fill="blue", font=("Arial", 8), tags="distance_text")

    def get_absolute_positions(self):
        """Get absolute positions of all elements relative to reference point"""
        if not self.reference_point:
            return None

        ref_x, ref_y = self.reference_point
        positions = {
            'reference_point': {'x': ref_x, 'y': ref_y},
            'elements': []
        }

        for element in self.elements:
            abs_pos = {
                'type': element['type'],
                'text': element['text'],
                'absolute_x': element['x'],
                'absolute_y': element['y'],
                'relative_x': element['x'] - ref_x,
                'relative_y': element['y'] - ref_y,
                'distance_from_ref': ((element['x'] - ref_x)**2 + (element['y'] - ref_y)**2)**0.5
            }
            positions['elements'].append(abs_pos)

        return positions

    def run(self):
        """Run the application"""
        try:
            print("Shape Positioning Tool started. Close the window when finished.")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.running:
                self.root.quit()
                self.root.destroy()

if __name__ == "__main__":
    app = ShapePositioningTool()
    app.run()