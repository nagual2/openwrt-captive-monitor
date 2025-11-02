@echo off
chcp 65001 > nul
git commit --amend -m "fix: исправление форматирования Markdown файлов" --no-edit
git push --force origin main
