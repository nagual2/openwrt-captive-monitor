@echo off
cd /d "%~dp0"

echo Добавляю изменения в Git...
git add .

echo Создаю коммит...
git commit -m "Удаление временных файлов и обновление документации"

echo Отправляю изменения на GitHub...
git push origin main

echo Готово!
pause
