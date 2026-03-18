# Captive Portal Daemon Docker Image - Lightweight Version
FROM python:3.12-slim

# Установка минимальных системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tini procps && \
    rm -rf /var/lib/apt/lists/*

# Python зависимости (только requests)
RUN pip install --no-cache-dir requests==2.31.0

# Рабочая директория
WORKDIR /app

# Копирование lightweight daemon скрипта
COPY tools/simple_captive_daemon.py /app/

# Директории для логов
RUN mkdir -p /var/log

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL=60

# Healthcheck
HEALTHCHECK --interval=120s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f simple_captive_daemon.py || exit 1

# tini как init для правильной обработки сигналов
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "-u", "/app/simple_captive_daemon.py"]
