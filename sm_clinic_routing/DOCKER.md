# ArtKnit в Docker

Проект упакован в Docker **без изменений исходного кода** — добавлены только
инфраструктурные файлы (`Dockerfile`, `docker-compose.yml`, `entrypoint.sh`,
`.dockerignore`, `.gitattributes`, `Makefile.docker`).

Работает одинаково на **Linux** и **Windows** (Docker Desktop / WSL2).

## Быстрый старт

```bash
# 1. Поднять веб-сервер (Django) — http://localhost:8000
docker compose up -d --build

# 2. Полный цикл make all (setup + parse + test-real + demo + manager)
docker compose run --rm artknit make all

# 3. Отдельные make-цели — любые, как в Makefile
docker compose run --rm artknit make demo
docker compose run --rm artknit make test
docker compose run --rm artknit make parse
docker compose run --rm artknit make test-real
docker compose run --rm artknit make manager
docker compose run --rm artknit make audit
docker compose run --rm artknit make metrics

# 4. Остановить сервер
docker compose down
```

Альтернатива через make-обёртку (та же механика):

```bash
make -f Makefile.docker up     # веб-сервер
make -f Makefile.docker all    # make all
make -f Makefile.docker demo   # демо
make -f Makefile.docker down
```

## Что делает образ при сборке

| Шаг | Действие |
|---|---|
| Базовый образ | `python:3.12-slim` |
| Системные пакеты | `make`, `gcc`, `g++` |
| Python-зависимости | `pip install -r requirements.txt` (системный Python) |
| venv | `python3 -m venv --system-site-packages venv` — Makefile вызывает `venv/bin/python`, пакеты видны через system-site-packages |
| Инициализация | `make demo` — демо-экраны генерируются прямо в образ |
| Точка входа | `entrypoint.sh`: без аргументов → веб-сервер; `make …` → проброс в make |

## Как работает entrypoint

```
docker compose up                        → python manage.py runserver 0.0.0.0:8000
docker compose run --rm artknit make X   → make X внутри контейнера
docker compose run --rm artknit bash     → произвольная команда
```

## Данные

Папка `output/` (HTML-экраны, метрики, `routes_audit.jsonl`) смонтирована
с хоста в контейнер:

```yaml
volumes:
  - ./output:/app/output
```

Поэтому результаты генерации сохраняются на устройстве даже после
`docker compose down`. Конфиги (`config/*.yaml`) лежат в репозитории и
пересобираются командой `make parse`.

## Порт

По умолчанию веб-сервер слушает порт `8000`. Поменять:

```bash
ARTKNIT_PORT=8080 docker compose up -d
```

## Совместимость с Windows

- `.gitattributes` принудительно хранит `*.sh`, `Makefile`, `Dockerfile`
  в LF — на Windows это защищает от CRLF-ошибок (shebang, табы в make).
- `chmod +x` выполняется в Dockerfile, поэтому биты прав не зависят
  от файловой системы хоста.
- `docker compose` v2 входит в Docker Desktop; WSL2-бэкенд обязателен
  (стандартная установка).

## Требования

- Docker Engine 20.10+ / Docker Desktop 4+
- Docker Compose v2 (входит в Docker Desktop; для Linux — плагин `docker-compose-plugin`)