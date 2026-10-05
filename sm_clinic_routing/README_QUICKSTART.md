# 🚀 ArtKnit — как запустить на любом компьютере (подробная инструкция)

> Второй README проекта: пошаговое руководство «для начинающих» с картинками-схемами.
> Подходит для **Windows, macOS и Linux**. Команды везде одинаковые — просто копируйте и вставляйте.
>
> 📌 Основной README с описанием проекта: [`README.md`](README.md)
> 📌 Краткая справка по Docker: [`DOCKER.md`](DOCKER.md)

---

## 🧭 Карта пути (схема 1): от скачивания до открытого сайта

```mermaid
flowchart LR
    A[📥 Скачал проект<br/>ZIP или git clone] --> B[🐳 Установил Docker]
    B --> C[💻 Открыл терминал<br/>в папке sm_clinic_routing]
    C --> D[⚙️ docker compose up -d --build]
    D --> E[🌐 Браузер:<br/>http://localhost:8000]
    E --> F[✅ Страница ArtKnit открылась]

    style A fill:#E8F5EE,stroke:#13AB7B
    style B fill:#E8F5EE,stroke:#13AB7B
    style C fill:#E8F5EE,stroke:#13AB7B
    style D fill:#FFF4E6,stroke:#F5B400
    style E fill:#E8F5EE,stroke:#13AB7B
    style F fill:#D6F5E8,stroke:#0F9668,stroke-width:2px
```

**Три простых шага:**
1. **Скачать** проект (кнопка `Code → Download ZIP`, распаковать).
2. **Установить** бесплатную программу Docker (один раз).
3. **Запустить** две команды и открыть браузер.

---

## 🧰 Что понадобится

| Что | Зачем |
|---|---|
| Компьютер | Windows 10/11, macOS или Linux — любой |
| Программа **Docker** | Собирает и запускает проект в изолированной «коробке» |
| **Интернет** | Только в первый раз — Docker скачает нужные компоненты |

Ничего другого устанавливать не нужно: Python, базы данных и все библиотеки Docker принесёт сам.

---

## ⚙️ Шаг 1. Установите Docker

### Windows
1. Откройте сайт: `https://www.docker.com/products/docker-desktop/`
2. Нажмите **Download for Windows**.
3. Запустите установщик: **Next → ОК → Install**.
4. Если попросит перезагрузиться — перезагрузитесь.
5. Запустите **Docker Desktop**. В трее (справа внизу) появится иконка кита 🐳. Когда она перестанет «мигать» — Docker готов.

### macOS
1. Тот же сайт → **Download for Mac**.
2. Перетащите Docker в папку «Программы».
3. Запустите **Docker Desktop**, дождитесь иконки кита вверху экрана.

### Linux (Ubuntu/Debian)
Откройте терминал и выполните по очереди:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
```

Разрешите себе пользоваться Docker без пароля (один раз):

```bash
sudo usermod -aG docker $USER
```

**Важно:** после этого выйдите из системы и войдите заново (или перезагрузитесь) — иначе права не применятся.

### ✅ Проверка для всех ОС

```bash
docker --version
```

- Видите `Docker version ...` → всё отлично, идём дальше.
- Видите `command not found` → вернитесь к установке.

---

## 💾 Шаг 2. Скачайте проект

1. Откройте страницу репозитория в GitHub.
2. Кнопка **Code** (зелёная, справа вверху) → **Download ZIP**.
3. Распакуйте архив (например, в «Загрузки» или «Документы»).

Внутри появится папка **sm_clinic_routing** — это и есть проект. Дальше мы работаем только с ней.

---

## 💻 Шаг 3. Откройте терминал в папке проекта

### Windows — самый простой способ
1. Откройте папку `sm_clinic_routing` в проводнике.
2. Кликните по **адресной строке** (строка сверху, где написано имя папки).
3. Сотрите текст, введите `cmd` и нажмите **Enter**.
4. Откроется чёрное окно терминала — оно уже «стоит» в правильной папке.

### macOS
1. Откройте папку `sm_clinic_routing` в Finder.
2. Правой кнопкой по папке → **Службы** → **Новый терминал в папке**.

### Linux
```bash
cd Путь/к/папке/sm_clinic_routing
```

**Как понять, что вы там:** в начале строки терминала написано `.../sm_clinic_routing`.

---

## 🚀 Шаг 4. Запустите сервер

Вставьте в терминал и нажмите **Enter**:

```bash
docker compose up -d --build
```

- **Первый раз** — 3–7 минут (Docker собирает «коробку»). Это нормально.
- **Все следующие разы** — несколько секунд.

Готово, когда увидите в конце:

```
✔ Container artknit  Started
```

### Что происходит в этот момент (схема 2)

```mermaid
flowchart TD
    A[docker compose up -d --build] --> B[Сборка образа<br/>python:3.12-slim]
    B --> C[Установка зависимостей<br/>pip install -r requirements.txt]
    C --> D[Создание venv для make-целей]
    D --> E[Генерация демо-экранов<br/>make demo]
    E --> F[Запуск контейнера artknit]
    F --> G[entrypoint.sh]
    G --> H[Веб-сервер Django<br/>порт 8000]

    style A fill:#FFF4E6,stroke:#F5B400
    style H fill:#D6F5E8,stroke:#0F9668,stroke-width:2px
```

---

## 🌐 Шаг 5. Откройте браузер

1. Откройте Chrome, Edge, Firefox или Safari.
2. В адресной строке (строка вверху) введите:

```
http://localhost:8000
```

3. Нажмите **Enter**.

Вы увидите страницу **«ArtKnit — Маршрутизация протоколов УЗИ»** с формой и боковым меню. 🎉

### Как устроена система (схема 3)

```mermaid
flowchart LR
    U[👤 Пользователь<br/>браузер] --> W[Веб-сервер Django<br/>http://localhost:8000]
    W --> P[Форма: текст протокола УЗИ]
    P --> C[Ядро маршрутизации<br/>src/: извлечение → триггеры → маршрут]
    C --> O[Результаты<br/>output/: экран врача, экран пациента, журнал аудита]
    O --> W
    W --> U

    style U fill:#E8F5EE,stroke:#13AB7B
    style W fill:#FFF4E6,stroke:#F5B400
    style C fill:#E8F5EE,stroke:#13AB7B
    style O fill:#E8F5EE,stroke:#13AB7B
```

---

## 🧪 Шаг 6. Попробуйте (по желанию)

1. На главной странице найдите список **«Демо-протокол»**.
2. Выберите любой пункт, например *«Кардио (ГЛЖ + ФВ 45%)»* — текст сам подставится в форму.
3. Нажмите **«Обработать»**.
4. Появится маршрут: какой врач нужен, насколько срочно, в какой срок.
5. Нажмите **«Экран врача»** или **«Экран пациента»** — откроются готовые экраны.

---

## 🛑 Шаг 7. Остановите сервер

Когда закончите, вернитесь в терминал:

```bash
docker compose down
```

- Сервер остановится, страница перестанет открываться.
- Все результаты останутся в папке `output/` — ничего не потеряется.
- Для повторного запуска — снова Шаги 4–5 (теперь за секунды).

---

## 🆘 Если что-то не получается (схема 4: дерево решений)

```mermaid
flowchart TD
    S[Ошибка при запуске?] --> T1{docker: command not found?}
    T1 -->|Да| R1[Установить Docker → Шаг 1]
    T1 -->|Нет| T2{permission denied<br/>/var/run/docker.sock?}
    T2 -->|Да| R2[sudo usermod -aG docker $USER<br/>затем newgrp docker или перелогиниться]
    T2 -->|Нет| T3{«port is already allocated»?}
    T3 -->|Да| R3[ARTKNIT_PORT=8080 docker compose up -d<br/>открыть http://localhost:8080]
    T3 -->|Нет| T4{Docker Desktop не запущен?}
    T4 -->|Да| R4[Запустить Docker Desktop,<br/>дождаться иконки кита]
    T4 -->|Нет| R5[Перечитать Шаги 2–4,<br/>проверить папку sm_clinic_routing]

    style S fill:#FDECEA,stroke:#E53935
    style R1 fill:#FFF4E6,stroke:#F5B400
    style R2 fill:#FFF4E6,stroke:#F5B400
    style R3 fill:#FFF4E6,stroke:#F5B400
    style R4 fill:#FFF4E6,stroke:#F5B400
    style R5 fill:#FFF4E6,stroke:#F5B400
```

### Таблица проблем

| Что вы видите | Причина | Решение |
|---|---|---|
| `docker: command not found` | Docker не установлен | Вернитесь к Шагу 1 |
| `permission denied ... /var/run/docker.sock` | Нет прав на Docker (Linux) | `sudo usermod -aG docker $USER`, затем `newgrp docker` или перелогиниться |
| «port is already allocated» | Порт 8000 занят другой программой | `ARTKNIT_PORT=8080 docker compose up -d`, открыть `http://localhost:8080` |
| Ошибка про WSL2 (Windows) | Не установлен бэкенд WSL2 | При установке Docker Desktop согласиться на WSL2, перезагрузить ПК |
| Сервер не стартует | Docker Desktop выключен | Запустить Docker Desktop, дождаться иконки кита 🐳, повторить запуск |
| Страница не открывается | Нужно проверить статус | `docker compose ps` — контейнер должен быть `Up` |

---

## 🧰 Шпаргалка команд

| Хочу… | Команда |
|---|---|
| Запустить сервер (если уже собирал) | `docker compose up -d` |
| Собрать и запустить с нуля | `docker compose up -d --build` |
| Проверить статус | `docker compose ps` |
| Посмотреть логи | `docker compose logs artknit` |
| Остановить сервер | `docker compose down` |
| Пересобрать «коробку» | `docker compose build` |
| Полный цикл проверки проекта | `docker compose run --rm artknit make all` |
| Прогнать тесты | `docker compose run --rm artknit make test` |
| Демо-генерация HTML | `docker compose run --rm artknit make demo` |
| Любая make-команда | `docker compose run --rm artknit make <имя>` |
| Открыть терминал внутри контейнера | `docker compose run --rm artknit bash` |

> 💡 **Совет:** команды `make` можно набирать и через обёртку:
> `make -f Makefile.docker all`  — работает точно так же.

---

## 📁 Что остаётся на компьютере

```mermaid
flowchart LR
    V[Папка sm_clinic_routing] --> O[output/<br/>экран врача, пациента,<br/>метрики, журнал аудита]
    V --> C[config/<br/>правила маршрутизации YAML]
    V --> S[src/ + web/ + webapp/<br/>код системы и веб-интерфейса]

    style V fill:#E8F5EE,stroke:#13AB7B
    style O fill:#FFF4E6,stroke:#F5B400
    style C fill:#E8F5EE,stroke:#13AB7B
    style S fill:#E8F5EE,stroke:#13AB7B
```

Все результаты генерации сохраняются в папке **`output/`** — она на вашем диске, поэтому после `docker compose down` данные остаются.

**Удачи! 🚀 Если сделали всё по шагам — сервер обязательно запустится.**