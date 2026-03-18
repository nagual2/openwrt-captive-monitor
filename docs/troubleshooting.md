# Устранение неполадок

## Основные

- Если команды зависают из‑за пейджера или ввода, в WSL установи:
  `GIT_PAGER=cat`, `PAGER=cat`, `DEBIAN_FRONTEND=noninteractive`.
- При падении CI сначала смотри логи: `gh run view <id> --log`.

## Дополнительные

- Для долгих job в GitHub Actions используй `timeout-minutes` и `concurrency`.
- Проблемы SDK и Docker‑окружения разбирать по `docker_guide.md`.
