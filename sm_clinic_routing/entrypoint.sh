#!/bin/sh
# ============================================================
# entrypoint.sh — точка входа контейнера ArtKnit
#
#   docker compose up                          → веб-сервер на :8000
#   docker compose run --rm artknit make demo  → любой make-таргет
#   docker compose run --rm artknit bash       → произвольная команда
# ============================================================
set -e
cd /app

# output/ может быть смонтирован с хоста как пустой том
mkdir -p /app/output

if [ "$#" -eq 0 ]; then
    echo "🚀 ArtKnit: веб-сервер на http://127.0.0.1:8000"
    exec python manage.py runserver 0.0.0.0:8000
fi

case "$1" in
    make)
        shift
        exec make "$@"
        ;;
    *)
        exec "$@"
        ;;
esac