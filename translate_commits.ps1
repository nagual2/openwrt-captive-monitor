# Скрипт для перевода сообщений коммитов
# Создаем бэкап текущей ветки
$backupBranch = "backup-before-translation-$(Get-Date -Format 'yyyyMMddHHmmss')"
git branch $backupBranch
Write-Host "Создана резервная копия ветки: $backupBranch" -ForegroundColor Green

# Функция для перевода сообщений
function Translate-CommitMessage {
    param([string]$message)
    
    # Словарь для перевода
    $translations = @{
        'исправление' = 'fix'
        'форматирования' = 'formatting'
        'Markdown' = 'Markdown'
        'удаление' = 'remove'
        'временных файлов' = 'temporary files'
        'удалён' = 'removed'
        'бинарный файл' = 'binary file'
        'удалены' = 'removed'
        'лишние логи' = 'excessive logs'
        'файлов' = 'files'
        'и' = 'and'
    }
    
    # Применяем замены
    $newMessage = $message
    foreach ($key in $translations.Keys) {
        $newMessage = $newMessage -replace $key, $translations[$key]
    }
    
    return $newMessage.Trim()
}

# Получаем список коммитов с русскими сообщениями
$commits = git log --all --grep='[а-яА-Я]' --pretty=format:'%H %s'

if (-not $commits) {
    Write-Host "Коммиты с русскими сообщениями не найдены." -ForegroundColor Green
    exit 0
}

# Переводим сообщения
foreach ($commit in $commits) {
    $commitHash = $commit.Split(' ')[0]
    $originalMessage = $commit.Substring($commit.IndexOf(' ') + 1)
    $translatedMessage = Translate-CommitMessage -message $originalMessage
    
    Write-Host "Commit: $commitHash" -ForegroundColor Cyan
    Write-Host "Original: $originalMessage" -ForegroundColor Yellow
    Write-Host "Translated: $translatedMessage" -ForegroundColor Green
    Write-Host "---"
    
    # Изменяем сообщение коммита
    git filter-branch -f --msg-filter "if [ `git rev-parse $GIT_COMMIT` = '$commitHash' ]; then echo '$translatedMessage'; else cat; fi" --tag-name-filter cat -- --all
}

Write-Host "\nПеревод завершен. Проверьте изменения и выполните 'git push --force' для обновления удаленного репозитория." -ForegroundColor Green
Write-Host "Исходная ветка сохранена как: $backupBranch" -ForegroundColor Yellow
