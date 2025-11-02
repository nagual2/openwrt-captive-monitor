@echo off
cd /d "%~dp0"

echo Removing files...
git rm "how --name-only e873948"
git rm "how --oneline a9ae1e5~1"

echo Adding to .gitignore...
echo how --*>>.gitignore
git add .gitignore

echo Committing changes...
git commit -m "chore: remove temporary git output files"

echo Pushing to GitHub...
git push origin main

echo Done!
pause
