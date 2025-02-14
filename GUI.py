import tkinter as tk 
from tkinter import ttk, Toplevel
from PIL import Image, ImageTk
import os 

#Global Variables 
selectionbar_color = '#eff5f6'
sidebar_color = '#F5E1FD'
header_color = '#53366b'
visualisation_frame_color = '#ffffff'
#Root Window 
class GUI(tk.Tk):
    
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Data Collection App")
        # Basic App Layout 
        self.geometry("1100x700")
        self.resizable(0,0)
        self.title('Data Collection System')
        self.config(background=selectionbar_color)

        #SideBar
        self.sidebar = tk.Frame(self, bg=header_color)
        self.sidebar.place(relx=0, rely=0, relwidth=0.3, relheight=1)

        #Branding Frame
        self.brand_frame = tk.Frame(self.sidebar, bg=sidebar_color)
        self.brand_frame.place(relx=0, rely=0, relwidth=1, relheight=0.15)

        sidebar_title = tk.Label(self.brand_frame,
                            text='Multisensory',
                            bg=sidebar_color,
                            font=("", 25, "bold")
                            )
        sidebar_title.place(x=55, y=27, anchor="w")

        sidebar_title = tk.Label(self.brand_frame,
                            text='Tests',
                            bg=sidebar_color,
                            font=("", 25, "bold")
                            )
        sidebar_title.place(x=100, y=70, anchor="w")

        #Submenu Frame 

        self.submenu_frame = tk.Frame(self.sidebar, bg=sidebar_color)
        self.submenu_frame.place(relx=0, rely=0.2, relwidth=1, relheight=0.85)
        submenu1 = SidebarSubMenu(self.submenu_frame,
                                            sub_menu_heading='Experiment 1',
                                            sub_menu_options=["Unisensory Neutral Visual",
                                                            "Unisensory Alcohol Visual",
                                                            "Multisensory Neutral Visual & Olfactory",
                                                            "Multisensory Alcohol Visual & Olfactory",
                                                            "Multisensory Neutral Visual, Tactile & Olfactory",
                                                            "Multisensory Alcohol Visual, Tactile & Olfactory",
                                                            ]
                                            )
        submenu1.options["Unisensory Neutral Visual"].config(
            command=lambda: self.show_frame(Unisensory_Neutral_Visual)
        )
        submenu1.options["Unisensory Alcohol Visual"].config(
            command=lambda: self.show_frame(Unisensory_Alcohol_Visual)
        )
        submenu1.options["Multisensory Neutral Visual & Olfactory"].config(
            command=lambda: self.show_frame(Multisensory_Neutral_Visual_and_Olfactory)
        )
        submenu1.options["Multisensory Alcohol Visual & Olfactory"].config(
            command=lambda: self.show_frame(Multisensory_Alcohol_Visual_and_Olfactory)
        )
        submenu1.options["Multisensory Neutral Visual, Tactile & Olfactory"].config(
            command=lambda: self.show_frame(Multisensory_Neutral_Visual_Tactile_Olfactory)
        )
        submenu1.options["Multisensory Alcohol Visual, Tactile & Olfactory"].config(
            command=lambda: self.show_frame(Multisensory_Alcohol_Visual_Tactile_Olfactory)
        )

        submenu1.place(relx=0, rely=0.025, relwidth=1, relheight=0.65)

        #Main Frame 
        
        main_frame = tk.Frame(self)
        main_frame.place(relx=0.3, rely=0, relwidth=0.7, relheight=1)

        #Multi Page Settings

        main_frame = tk.Frame(self)
        main_frame.place(relx=0.3, rely=0, relwidth=0.7, relheight=1)
        
        #Adding Frames to the Main Frame 
        self.frames = {}

        for F in (Unisensory_Neutral_Visual, Unisensory_Alcohol_Visual, Multisensory_Neutral_Visual_and_Olfactory, Multisensory_Alcohol_Visual_and_Olfactory, Multisensory_Neutral_Visual_Tactile_Olfactory, Multisensory_Alcohol_Visual_Tactile_Olfactory): 
            frame = F(main_frame, self)
            self.frames[F] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.show_frame(Unisensory_Neutral_Visual)
    def show_frame(self,cont):
        
        #allows us to switch between frames
        
        frame = self.frames[cont]
        frame.tkraise()
        
class Unisensory_Neutral_Visual(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        top_frame(self, title="Unisensory Neutral Visual")
        middle_frame(self)
        bottom_frame(self)
class Unisensory_Alcohol_Visual(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Unisensory Alcohol Visual", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)
        top_frame(self, title="Unisensory Alcohol Visual")
        middle_frame(self)
        bottom_frame(self)

class Multisensory_Neutral_Visual_and_Olfactory(tk.Frame):
     def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Multisensory Neutral Visual & Olfactory", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)
        top_frame(self, title="Multisensory Neutral Visual & Olfactory")
        middle_frame(self)
        bottom_frame(self)

class Multisensory_Alcohol_Visual_and_Olfactory(tk.Frame):
     def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Multisensory Alcohol Visual & Olfactory", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)
        top_frame(self, title="Multisensory Alcohol Visual & Olfactory")
        middle_frame(self)
        bottom_frame(self)

class Multisensory_Neutral_Visual_Tactile_Olfactory(tk.Frame):
     def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Multisensory Neutral Visual, Tactile & Olfactory", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)
        top_frame(self, title="Multisensory Neutral Visual, Tactile & Olfactory")
        middle_frame(self)
        bottom_frame(self)

class Multisensory_Alcohol_Visual_Tactile_Olfactory(tk.Frame):
     def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Multisensory Alcohol Visual, Tactile & Olfactory", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)
        top_frame(self, title="Multisensory Alcohol Visual, Tactile & Olfactory")
        middle_frame(self)
        bottom_frame(self)

class top_frame(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent)
        #top part of frame/ should include start, stop, pause, and other features to be added later 
        self.place(in_=parent, relx=0, rely=0, relwidth=1, relheight=.20)
        label = ttk.Label(self, background = 'purple')
        label.place(in_=self, relx=0, rely=0, relwidth=1, relheight=1)
        header = ttk.Label(self, background='purple', text=title, font=("Helvetica", 25, "bold"))
        header.place(anchor="center", relx=.5, rely=.25)
        start_button = ttk.Button(self, text="Start")
        start_button.place(relx=.125,rely=.5)
        stop_button = ttk.Button(self, text="Stop")
        stop_button.place(relx=.05,rely=.75)
        pause_button = ttk.Button(self, text="Pause")
        pause_button.place(relx=.2,rely=.75)
        vr_button = ttk.Checkbutton(self, text="VR")
        vr_button.place(relx=.785,rely=.5)
        display_button = ttk.Checkbutton(self, text="Display", command=self.open_secondary_gui)        
        display_button.place(relx=.70,rely=.75)
        Viewing_Booth_Button = ttk.Checkbutton(self, text="Viewing Booth")
        Viewing_Booth_Button.place(relx=.85,rely=.75)    

    def open_secondary_gui(self):
        display = DisplayWindow(self)
        display.grab_set()
        
class DisplayWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.geometry("700x700")
        self.show_display()
        self.title("Display App")
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

class middle_frame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
         
        self.place(in_=parent, relx=0, rely=.2, relwidth=1, relheight=.70)
        label = ttk.Label(self, background = '#CBC3E3')
        label.place(in_=self, relx=0, rely=0, relwidth=1, relheight=1)

class bottom_frame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
         
        self.place(in_=parent, relx=0, rely=.9, relwidth=1, relheight=.10)
        label = ttk.Label(self, background = '#bc85fa')
        label.place(in_=self, relx=0, rely=0, relwidth=1, relheight=1)

        Visual = ttk.Checkbutton(self, text='Visual')
        Visual.place(relx=.1, rely=.25, relwidth=.1, relheight=.5)
        Olfactory = ttk.Checkbutton(self, text='Olfactory')
        Olfactory.place(relx=.25, rely=.25, relwidth=.1, relheight=.5)
        Tactile = ttk.Checkbutton(self, text='Tactile')
        Tactile.place(relx=.4, rely=.25, relwidth=.1, relheight=.5)
        Input_Keyboard = ttk.Checkbutton(self, text='Input Keyboard')
        Input_Keyboard.place(relx=.55, rely=.25, relwidth=.15, relheight=.5)
        Eye_Tracker = ttk.Checkbutton(self, text='Eye Tracker')
        Eye_Tracker.place(relx=.75, rely=.25, relwidth=.15, relheight=.5)

class SidebarSubMenu(tk.Frame):
    """
    A submenu which can have multiple options and these can be linked with
    functions.
    """
    def __init__(self, parent, sub_menu_heading, sub_menu_options):
        """
        parent: The frame where submenu is to be placed
        sub_menu_heading: Heading for the options provided
        sub_menu_operations: Options to be included in sub_menu
        """
        tk.Frame.__init__(self, parent)
        self.config(bg=sidebar_color)
        self.sub_menu_heading_label = tk.Label(self,
                                               text=sub_menu_heading,
                                               bg=sidebar_color,
                                               fg="#333333",
                                               font=("Arial", 10)
                                               )
        self.sub_menu_heading_label.place(x=30, y=10, anchor="w")

        sub_menu_sep = ttk.Separator(self, orient='horizontal')
        sub_menu_sep.place(x=30, y=30, relwidth=0.8, anchor="w")

        self.options = {}
        for n, x in enumerate(sub_menu_options):
            self.options[x] = tk.Button(self,
                                        text=x,
                                        bg=sidebar_color,
                                        font=("Arial", 9, "bold"),
                                        bd=0,
                                        cursor='hand2',
                                        activebackground='#ffffff',
                                        )
            self.options[x].place(x=30, y=45 * (n + 1), anchor="w")
        
root = GUI()
root.mainloop()