import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

class ImageAnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        
        # Initialize variables
        self.image = None
        self.tk_image = None
        self.rectangles = []
        self.start_x = None
        self.start_y = None
        self.drawing = False
        self.class_label = "Disease Class 1"
        self.annotations = []
        self.image_path = None
        self.zoom_factor = 1.0
        self.canvas_x_offset = 0
        self.canvas_y_offset = 0

        # Create a canvas to draw on
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        # Add buttons for loading image and saving annotations
        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack()
        
        self.save_button = tk.Button(root, text="Save Annotations", command=self.save_annotations)
        self.save_button.pack()
        
        self.undo_button = tk.Button(root, text="Undo Last Annotation", command=self.undo_last_annotation)
        self.undo_button.pack()
        
        self.class_label_var = tk.StringVar(root)
        self.class_label_var.set("Disease Class 1")
        self.class_dropdown = tk.OptionMenu(root, self.class_label_var, "Disease Class 1", "Disease Class 2", "Disease Class 3")
        self.class_dropdown.pack()

        # Zoom in/out buttons
        self.zoom_in_button = tk.Button(root, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack()
        
        self.zoom_out_button = tk.Button(root, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack()

    def load_image(self):
        """Load an image and display it on the canvas."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_in(self):
        """Zoom into the image by increasing the zoom factor."""
        self.zoom_factor *= 1.2
        self.update_image()

    def zoom_out(self):
        """Zoom out of the image by decreasing the zoom factor."""
        self.zoom_factor /= 1.2
        self.update_image()

    def update_image(self):
        """Update the displayed image according to the current zoom factor."""
        if self.image:
            # Apply zoom
            width, height = self.image.size
            new_size = (int(width * self.zoom_factor), int(height * self.zoom_factor))
            zoomed_image = self.image.resize(new_size, Image.ANTIALIAS)
            self.tk_image = ImageTk.PhotoImage(zoomed_image)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def start_rectangle(self, event):
        """Start drawing a rectangle."""
        self.start_x = event.x
        self.start_y = event.y
        self.drawing = True

    def draw_rectangle(self, event):
        """Draw the rectangle while dragging the mouse."""
        if self.drawing:
            self.canvas.delete("temp")  # Remove temporary rectangle
            self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", tags="temp")

    def end_rectangle(self, event):
        """Finish drawing the rectangle and save its coordinates."""
        if self.drawing:
            x1, y1, x2, y2 = self.start_x, self.start_y, event.x, event.y
            class_label = self.class_label_var.get()
            self.rectangles.append((x1, y1, x2, y2, class_label))
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red")
            self.drawing = False

    def undo_last_annotation(self):
        """Remove the last drawn bounding box."""
        if self.rectangles:
            self.rectangles.pop()
            self.canvas.delete("all")
            self.update_image()  # Redraw the image
            for rect in self.rectangles:
                x1, y1, x2, y2, _ = rect
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="red")

    def save_annotations(self):
        """Save the annotations to a file."""
        if not self.rectangles:
            messagebox.showwarning("No Annotations", "No annotations to save.")
            return
        
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if save_path:
            annotations = []
            for rect in self.rectangles:
                x1, y1, x2, y2, label = rect
                annotations.append({"bbox": [x1, y1, x2, y2], "class": label})
            
            with open(save_path, "w") as file:
                json.dump(annotations, file, indent=4)
            
            # Optionally save in Pascal VOC XML format
            self.save_pascal_voc()

    def save_pascal_voc(self):
        """Save annotations in Pascal VOC XML format."""
        if not self.rectangles or not self.image_path:
            return
        
        # Create the root XML element
        root = ET.Element("annotation")
        
        # Get image file name and size
        filename = os.path.basename(self.image_path)
        image = Image.open(self.image_path)
        width, height = image.size
        
        ET.SubElement(root, "folder").text = "images"
        ET.SubElement(root, "filename").text = filename
        ET.SubElement(root, "path").text = self.image_path
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(width)
        ET.SubElement(size, "height").text = str(height)
        ET.SubElement(size, "depth").text = "3"
        
        # Add objects (annotations)
        for rect in self.rectangles:
            x1, y1, x2, y2, label = rect
            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text = label
            ET.SubElement(obj, "pose").text = "Unspecified"
            ET.SubElement(obj, "truncated").text = "0"
            ET.SubElement(obj, "difficult").text = "0"
            bndbox = ET.SubElement(obj, "bndbox")
            ET.SubElement(bndbox, "xmin").text = str(x1)
            ET.SubElement(bndbox, "ymin").text = str(y1)
            ET.SubElement(bndbox, "xmax").text = str(x2)
            ET.SubElement(bndbox, "ymax").text = str(y2)
        
        # Convert the XML structure to a string and pretty print
        tree = ET.ElementTree(root)
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml()
        
        # Save XML to file
        xml_save_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML Files", "*.xml")])
        if xml_save_path:
            with open(xml_save_path, "w") as xml_file:
                xml_file.write(xml_str)
            print(f"Pascal VOC XML saved at {xml_save_path}")

    def run(self):
        """Run the annotation tool."""
        # Bind mouse events for drawing rectangles
        self.canvas.bind("<ButtonPress-1>", self.start_rectangle)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_rectangle)

        self.root.mainloop()

if __name__ == "__main__":
    # Initialize the Tkinter window
    root = tk.Tk()
    annotation_tool = ImageAnnotationTool(root)
    annotation_tool.run()