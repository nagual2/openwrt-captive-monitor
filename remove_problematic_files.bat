@echo off
cd /d "%~dp0"

echo Удаление файлов...

echo Удаляю "how --name-only e873948"...
del "how --name-only e873948"
if %ERRORLEVEL% NEQ 0 (
    echo Не удалось удалить файл 1
    pause
    exit /b 1
)

echo Удаляю "how --oneline a9ae1e5~1"...
del "how --oneline a9ae1e5~1"
if %ERRORLEVEL% NEQ 0 (
    echo Не удалось удалить файл 2
    pause
    exit /b 1
)

echo Все файлы успешно удалены!
pause
