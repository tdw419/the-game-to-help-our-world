#!/bin/bash
git init
git add .
git commit -m "PXLDISK GitHub-ready mirror package"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pxldisk-mirror.git
git push -u origin main
