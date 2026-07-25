# Captive Portal Daemon Docker Image - Optimized Version
# Based on Debian (bookworm)
FROM python:3.11-slim-bookworm

# Установка системных зависимостей
# Chromium и chromium-driver для Selenium
# tini для корректной обработки сигналов
# procps для работы pkill
# Оптимизация Docker образа
# - Использование .dockerignore для уменьшения контекста
# - Очистка кэшей в одном слое
# - Минимальный набор зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    tini \
    procps \
    curl \
    iputils-ping \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libx11-xcb1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Установка Python зависимостей
RUN pip install --no-cache-dir selenium==4.15.2 requests

# Рабочая директория
WORKDIR /app

# Copy optimized monitor + adaptive interval helpers
COPY tools/captive-portal-monitor-optimized.py tools/daemon_interval.py /app/

# Создание директорий для логов и данных
RUN mkdir -p /var/log /var/lib/captive-portal && \
    touch /var/log/captive_portal_auth.log && \
    chmod 666 /var/log/captive_portal_auth.log

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV RUNTIME_DIR=/var/lib/captive-portal
ENV LOG_FILE=/var/log/captive_portal_auth.log
ENV COOKIES_FILE=/var/lib/captive-portal/cookies.pkl
ENV COOKIES_META_FILE=/var/lib/captive-portal/cookies_meta.json

# Healthcheck
HEALTHCHECK --interval=120s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f captive-portal-monitor-optimized.py || exit 1

# tini как init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Запуск оптимизированного скрипта
# ВАЖНО: Так как это монитор, он может работать как daemon если зациклен, 
# либо вызываться периодически. В текущей реализации main() он делает одну проверку.
# Для Docker образа мы предполагаем использование в режиме daemon или с внешним планировщиком.
CMD ["python3", "-u", "/app/captive-portal-monitor-optimized.py"]
