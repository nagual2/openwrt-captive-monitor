# Project Preferences

## Language Preferences

- Communicate with the user in Russian
- Write all plans, documentation, and explanations in Russian
- Write git commit messages in English only

## Shell and Tools Preferences

- Use PowerShell for Windows-native commands
- Run git commands directly using git CLI (without WSL prefix)
- Use WSL 2 for Linux utilities (grep, sed, awk, bash scripts, etc.)
- WSL 2 is installed and working (version 2.6.1.0, kernel 6.6.87.2)
- Docker Desktop is installed and working (version 29.0.1)
- Docker uses WSL 2 backend for containers
- Python 3.12.10 is installed on Windows with pip 25.3
- Python 3.10.12 is installed in WSL
- Prefix Linux utility commands with `wsl` when running on Windows system
- Show commands before executing them for transparency

## Python Libraries

**Windows Python 3.12.10:**

- PyTorch 2.9.1+cpu (with torchvision 0.24.1+cpu, torchaudio 2.9.1+cpu)
- Transformers 4.57.3
- NumPy 2.3.5
- ✅ Verified: All libraries working correctly, tensor operations tested
- ✅ Verified: Transformers pipeline tested with sentiment analysis model

**WSL Python 3.10.12:**

- PyTorch 2.9.1+cpu (with torchvision 0.24.1+cpu, torchaudio 2.9.1+cpu)
- Transformers 4.57.3
- NumPy 2.1.2
- ✅ Verified: All libraries working correctly, tensor operations tested

## Docker Installation

**Windows Docker Desktop 29.0.1:**

- ✅ Verified: Docker daemon running
- ✅ Verified: hello-world container test passed
- Backend: WSL 2

**WSL Docker 28.2.2:**

- ✅ Verified: Docker client working
- ✅ Verified: hello-world container test passed
- Connected to Docker Desktop daemon

## Development Tools

**Windows:**

- Git 2.49.0.windows.1 ✅
- GitHub CLI 2.81.0 ✅ (authenticated as nagual2)

**WSL:**

- Bash 5.1.16 ✅
- GNU Make 4.3 ✅

## System Storage

- Disk C: 128GB total, ~70GB free (expanded from 59GB by removing recovery partition)
- Recovery partition was removed to expand system disk
- Sufficient space available for PyTorch and ML libraries installation

## Git Workflow

### Основной процесс

1. **Always work in feature branches** - never commit directly to main
2. **Create a new branch** for each feature or fix
3. **Make commits** with clear, descriptive messages in English
4. **Create Pull Request (PR)** for code review
5. **Check GitHub Actions** after PR creation:
   - If actions failed → fix issues and push fixes
   - If actions passed → proceed to merge
6. **Merge to main** (only after actions pass)
7. **Check GitHub Actions** after merge to main:
   - If actions failed → fix issues immediately
   - If actions passed → proceed to cleanup
8. **Delete feature branch** after successful merge

### Детальный workflow

```bash
# 1. Создать feature branch
git checkout -b feature/my-feature

# 2. Сделать изменения и коммиты
git add .
git commit -m "feat: add new feature"

# 3. Push ветки
git push origin feature/my-feature

# 4. Создать PR
gh pr create --title "feat: add new feature" --body "Description"

# 5. Проверить статус Actions
gh run list --branch feature/my-feature --limit 5

# 6. Если Actions упали - исправить
git add .
git commit -m "fix: resolve CI issues"
git push

# 7. Когда Actions прошли - мержить
gh pr merge --squash

# 8. Проверить статус Actions на main
gh run list --branch main --limit 5

# 9. Если Actions на main прошли - удалить ветку
git branch -d feature/my-feature
git push origin --delete feature/my-feature

# 10. Создать релиз (автоматически через auto-version-tag.yml)
# Релиз создастся автоматически при push в main
# Или запустить вручную:
gh workflow run "Auto Version Tag" --ref main

# 11. Проверить создание релиза
gh release list --limit 5
```

### Правила

- **Никогда не мержить** если Actions не прошли
- **Всегда проверять Actions** после merge в main
- **Немедленно исправлять** если Actions упали на main
- **Удалять feature branch** только после успешного merge и прохождения Actions
- **Создавать релиз** после успешного merge в main
- **Keep branches up to date** with main before merging

### Автоматическое создание релизов

После merge в main автоматически:
1. Запускается `auto-version-tag.yml`
2. Создаётся новый тег в формате `vYYYY.M.D.N`
3. Обновляются VERSION и PKG_VERSION
4. Создаётся GitHub Release
5. Запускается `tag-build-release.yml` для сборки артефактов

**Проверка релиза:**
```bash
# Посмотреть последние релизы
gh release list --limit 5

# Посмотреть детали последнего релиза
gh release view --web

# Проверить артефакты релиза
gh release view <tag> --json assets
```

## Git Access

All four access methods are configured and working:

1. **GitHub CLI (Windows)**: Authorized as nagual2, token scopes: gist, read:org, repo, workflow
2. **Git CLI (Windows)**: HTTPS access to github.com/nagual2/openwrt-captive-monitor.git
3. **GitHub CLI (WSL)**: ✅ Authorized as nagual2, HTTPS protocol configured
4. **Git (WSL)**: HTTPS access working

- Git access is configured for both HTTPS and SSH protocols
- GitHub Actions are enabled with workflow permissions
- ✅ **WSL GitHub Actions access verified**: Token has workflow permissions, can trigger and monitor runs
- When running workflows via gh CLI, always specify branch: `gh workflow run "name" --ref branch-name`
- For workflows requiring inputs, use: `gh api -X POST /repos/owner/repo/actions/workflows/ID/dispatches -f ref='branch'`
