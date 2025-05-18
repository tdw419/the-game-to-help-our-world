# black-vault/packager.py

import os

print("This script helps you package Pixel Vault into a standalone .exe")
print("Make sure you have installed pyinstaller: pip install pyinstaller")

entry_point = input("Enter the name of your main file (e.g., gui.py): ").strip()

if not os.path.exists(entry_point):
    print(f"File '{entry_point}' does not exist.")
else:
    os.system(f"pyinstaller --onefile --windowed {entry_point}")
    print("Packaging complete. Check the 'dist' folder for your .exe file.")
