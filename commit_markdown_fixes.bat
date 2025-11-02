@echo off
echo Adding changes to Git...
git add .

echo Creating commit...
git commit -m "fix: исправление форматирования Markdown файлов"

echo Pushing changes to GitHub...
git push origin main

echo Done!
pause
