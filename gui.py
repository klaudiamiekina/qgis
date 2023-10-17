import tkinter as tk
from tkinter import filedialog

def browse_file():
    file_path = filedialog.askopenfilename()
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)

def browse_folder():
    folder_path = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder_path)

# Tworzenie głównego okna aplikacji
root = tk.Tk()
root.title("Prosty GUI")

# Tworzenie etykiet i przycisków
file_label = tk.Label(root, text="Wybierz plik:")
file_label.pack()

file_entry = tk.Entry(root)
file_entry.pack()

file_button = tk.Button(root, text="Przeglądaj", command=browse_file)
file_button.pack()

folder_label = tk.Label(root, text="Wybierz folder:")
folder_label.pack()

folder_entry = tk.Entry(root)
folder_entry.pack()

folder_button = tk.Button(root, text="Przeglądaj", command=browse_folder)
folder_button.pack()

# Uruchomienie głównej pętli GUI
root.mainloop()
