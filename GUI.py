import tkinter as tk 
from tkinter import ttk

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
       
        # Header
        self.header = tk.Frame(self, bg=header_color)
        self.header.place(relx=0.3, rely=0, relwidth=0.7, relheight=0.1)

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
                                                            ]
                                            )
        submenu1.options["Unisensory Neutral Visual"].config(
            command=lambda: self.show_frame(Unisensory_Neutral_Visual)
        )
        submenu1.options["Unisensory Alcohol Visual"].config(
            command=lambda: self.show_frame(Frame2)
        )

        submenu1.place(relx=0, rely=0.025, relwidth=1, relheight=0.3)

        #Main Frame 
        
        main_frame = tk.Frame(self)
        main_frame.place(relx=0.3, rely=0.1, relwidth=0.7, relheight=0.9)

        #Multi Page Settings

        main_frame = tk.Frame(self)
        main_frame.place(relx=0.3, rely=0.1, relwidth=0.7, relheight=0.9)
        
        #Adding Frames to the Main Frame 
        self.frames = {}

        for F in (Unisensory_Neutral_Visual, Frame2): 
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
        label = tk.Label(self, text='Unisensory Neutral Visual', font=('Helvetica', 17))
        label.pack(fill=tk.BOTH)
class Frame2(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Unisensory Alcohol Visual", font=("Helvetica", 17))
        label.pack(fill=tk.BOTH)

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