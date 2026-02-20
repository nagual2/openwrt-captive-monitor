# Captive Portal Daemon Docker Image
FROM python:3.12-slim

# Установка системных зависимостей + Chrome в одном слое
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget gnupg ca-certificates curl tini procps && \
    wget -q -O /tmp/google-chrome.deb \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y --no-install-recommends /tmp/google-chrome.deb && \
    rm -f /tmp/google-chrome.deb && \
    rm -rf /var/lib/apt/lists/*

# Python зависимости
RUN pip install --no-cache-dir selenium==4.40.0

# Рабочая директория
WORKDIR /app

# Копирование daemon скрипта
COPY tools/captive_portal_daemon.py /app/

# Директории для логов и данных
RUN mkdir -p /var/log /var/lib

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL=60

# Healthcheck
HEALTHCHECK --interval=120s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f captive_portal_daemon.py || exit 1

# tini как init для правильной обработки сигналов
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "-u", "/app/captive_portal_daemon.py"]
