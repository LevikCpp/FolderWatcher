from tkinter import Tk
from gui import Window

def main():
    root = Tk()
    root.iconbitmap('C://Users//SGKing//vs code//Новая папка//logo.ico')
    app = Window(root)
    root.mainloop()

if __name__ == "__main__":
    main()
