@echo off
echo Удаление временных файлов...

if exist "how --name-only e873948" (
    del "how --name-only e873948"
    if %ERRORLEVEL% NEQ 0 (
        echo Ошибка при удалении файла 1
        exit /b 1
    )
)

if exist "how --oneline a9ae1e5~1" (
    del "how --oneline a9ae1e5~1"
    if %ERRORLEVEL% NEQ 0 (
        echo Ошибка при удалении файла 2
        exit /b 1
    )
)

echo Обновление .gitignore...
echo how --*>>.gitignore

echo Добавление изменений в Git...
git add .

echo Создание коммита...
git commit -m "fix: исправление форматирования Markdown и удаление временных файлов"

echo Отправка изменений на GitHub...
git push origin main

echo Готово!
pause
