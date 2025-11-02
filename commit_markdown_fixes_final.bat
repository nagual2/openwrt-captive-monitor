@echo off
echo Adding all changes to git...
git add .

echo Creating commit...
git commit -m "fix: исправление форматирования Markdown файлов (финальное)"

echo Pushing changes to GitHub...
git push origin main

echo Done! All Markdown files have been fixed and pushed.
