@echo off
echo Fixing Markdown files...

:: Install markdownlint if not installed
npm install -g markdownlint-cli

:: Run markdownlint with autofix
markdownlint "**/*.md" --fix

echo Markdown files have been formatted successfully.
pause
