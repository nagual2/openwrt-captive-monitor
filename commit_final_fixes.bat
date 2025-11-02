@echo off
echo Adding changes to Git...
git add .

echo Creating commit...
git commit -m "fix: исправление оставшихся проблем с форматированием Markdown"

echo Pushing changes to GitHub...
git push origin main

echo Done!
pause
