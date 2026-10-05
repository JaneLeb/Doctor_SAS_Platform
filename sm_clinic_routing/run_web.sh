#!/usr/bin/env bash
# ============================================================
# run_web.sh — запуск и остановка веб-интерфейса ArtKnit
#
#   ./run_web.sh          — запустить сервер
#   ./run_web.sh start    — то же самое
#   ./run_web.sh stop     — остановить сервер
#   PORT=8001 ./run_web.sh — запустить на другом порту
# ============================================================
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8000}"

# Ищем Python из виртуального окружения:
# сначала venv рядом с проектом (../.venv), затем venv внутри проекта
PY=""
for cand in ../.venv/bin/python venv/bin/python .venv/bin/python; do
  if [ -x "$cand" ]; then
    PY="$cand"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "❌ Виртуальное окружение не найдено."
  echo "   Создайте его один раз:"
  echo "   python3 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

case "${1:-start}" in
  start)
    echo "🚀 Запускаю сервер: http://127.0.0.1:${PORT}/"
    echo "   Остановка: Ctrl+C в этом терминале или ./run_web.sh stop"
    exec "$PY" manage.py runserver "$PORT" --noreload
    ;;
  stop)
    if pkill -f "manage.py runserver ${PORT}"; then
      echo "🛑 Сервер остановлен"
    else
      echo "ℹ️  Сервер и так не запущен"
    fi
    ;;
  *)
    echo "Использование: ./run_web.sh [start|stop]"
    ;;
esac