import tkinter as tk 
from tkinter import ttk, Toplevel
from PIL import Image, ImageTk
import os 

#Global Variables

#Root Window
class ImageDisplay:
    def show_display(self):
        #Getting the Image path and finding the image
        image_folder = os.path.join(os.path.dirname(__file__), 'Images')
        image = 'Beer.jpg'
        image_path = os.path.join(image_folder, image)
        image = Image.open(image_path)
        self.photo = ImageTk.PhotoImage(image)
        self.image_label = ttk.Label(self, image=self.photo)
        self.image_label.image = self.photo
        self.image_label.pack(fill=tk.BOTH)




#root = Display()
#root.mainloop()