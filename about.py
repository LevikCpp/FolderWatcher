from tkinter import Toplevel, Label
from tkinter.ttk import Style, Button, Label as TtkLabel
from PIL import Image, ImageTk

class about_fw(Toplevel):
    def __init__(self, parent, language, labels):
        super().__init__(parent)
        self.language = language
        self.labels = labels
        self.geometry('250x300')
        self.configure(bg='white')
        self.resizable(width=False, height=False)
        self.create_widgets()

    def create_widgets(self):
        style = Style()
        style.configure('Custom.TLabel', background='white', font=('Helvetica', 14))
        style.configure('Custom.TButton', foreground='black', background='white', font=('Helvetica', 12))
        
        image = Image.open("C://Users//SGKing//vs code//Новая папка//Безымянный.png").resize((200, 200))
        photo = ImageTk.PhotoImage(image)
        
        about_label = Label(self, image=photo, bg='white')
        about_label.image = photo
        about_label.grid(row=0, column=0, padx=20, pady=20)

        TtkLabel(self, text="Folder Watcher v1.0", style='Custom.TLabel').grid(row=1, column=0)
        Button(self, text="Close", command=self.destroy, style='Custom.TButton', takefocus=0).grid(row=2, column=0)