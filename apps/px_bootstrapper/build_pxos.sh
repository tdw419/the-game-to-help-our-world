#!/bin/bash

# Build PXOS_Sovereign for Linux, Windows, macOS
echo "Embedding zTXt assets..."
python3 embed_ztxt.py

echo "Assembling Linux bootstrapper..."
nasm -f elf64 bootstrap_linux.asm -o bootstrap_linux.o
ld bootstrap_linux.o -o PXOS_Sovereign

echo "Assembling Windows bootstrapper..."
nasm -f win64 bootstrap_windows.asm -o bootstrap_windows.o
ld bootstrap_windows.o -o PXOS_Sovereign.exe

echo "Compiling macOS bootstrapper..."
clang -framework CoreGraphics bootstrap_macos.c -o PXOS_Sovereign_macos
mkdir -p PXOS_Sovereign.app/Contents/MacOS
mv PXOS_Sovereign_macos PXOS_Sovereign.app/Contents/MacOS/PXOS_Sovereign

echo "Setting permissions..."
chmod +x PXOS_Sovereign
chmod +x PXOS_Sovereign.app/Contents/MacOS/PXOS_Sovereign

echo "Build complete. Run with:"
echo "Linux: sudo ./PXOS_Sovereign"
echo "Windows: PXOS_Sovereign.exe"
echo "macOS: ./PXOS_Sovereign.app/Contents/MacOS/PXOS_Sovereign"