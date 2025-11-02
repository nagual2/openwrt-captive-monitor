@echo off
chcp 65001 > nul
git commit --amend -m "fix: исправление форматирования Markdown и удаление временных файлов"
git push --force origin main
