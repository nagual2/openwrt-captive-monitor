# Скрипт для исправления сообщений коммитов
# Создаем бэкап текущей ветки
$backupBranch = "backup-before-fix-$(Get-Date -Format 'yyyyMMddHHmmss')"
git branch $backupBranch
Write-Host "Создана резервная копия ветки: $backupBranch" -ForegroundColor Green

# Список коммитов для исправления (хэш : новое сообщение)
$commitsToFix = @{
    "5a73e9e5e5a8d956e7d4f26f8c8809f56ea62817" = "fix: resolve remaining Markdown formatting issues"
    "795389d7c44af9d3fcc5d425305f48aeca1e85c4" = "fix: fix Markdown file formatting"
    "8fd560c786d031f155722352b033c98c6fe4e245" = "fix: fix Markdown formatting and remove temporary files"
    "92a9669" = "chore: remove Go 1.21.6 binary file"
    "bc12f8e" = "chore: remove excessive git logs"
}

# Перебираем коммиты и исправляем сообщения
foreach ($commitHash in $commitsToFix.Keys) {
    $newMessage = $commitsToFix[$commitHash]
    
    Write-Host "Исправление коммита: $commitHash" -ForegroundColor Cyan
    Write-Host "Новое сообщение: $newMessage" -ForegroundColor Green
    
    # Используем git filter-branch для изменения сообщения
    git filter-branch -f --msg-filter "if [ `git rev-parse $GIT_COMMIT` = $commitHash ]; then echo '$newMessage'; else cat; fi" --tag-name-filter cat -- --all
}

Write-Host "\nИсправление завершено. Проверьте изменения командой: git log" -ForegroundColor Green
Write-Host "Для отмены изменений: git reset --hard $backupBranch" -ForegroundColor Yellow
Write-Host "Для применения изменений: git push --force" -ForegroundColor Red
