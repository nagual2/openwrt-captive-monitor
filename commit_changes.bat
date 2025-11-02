@echo off
cd /d "%~dp0"
git add .
git commit -m "fix: cleanup markdown formatting"
git push origin main
