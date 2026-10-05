# ============================================================
# ArtKnit — система автоматической маршрутизации пациентов
#
# Сборка образа:      docker compose build
# Запуск веб-сервера: docker compose up
# Выполнить make:     docker compose run --rm artknit make <цель>
#
# Работает на Linux и Windows (Docker Desktop / WSL2).
# ============================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# make — для всех make-целей проекта;
# gcc/g++ — на случай сборки нативных колёс (pandas/numpy и т.п.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) Зависимости — отдельным слоем (переиспользуется кэш сборки)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 2) venv для make-целей: Makefile вызывает venv/bin/python.
#    --system-site-packages — пакеты берутся из системного Python,
#    поэтому make demo/parse/test работают сразу, без повторной установки.
RUN python3 -m venv --system-site-packages venv

# 3) Код проекта
COPY . .

# 4) Генерация демо-экранов прямо при сборке образа
RUN make demo || echo "⚠️  make demo на этапе сборки пропущен"

# 5) Точка входа (chmod обязателен для Windows-хостов: биты прав из git не переносятся)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]