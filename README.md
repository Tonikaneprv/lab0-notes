# Лаба 0 — свой сервис («Заметки»)

Маленькое приложение из трёх частей:

- **Бэкенд** — Python + Flask (`backend/app.py`). Эндпоинты `GET /api/notes` (читает из базы) и `POST /api/notes` (пишет в базу).
- **Фронтенд** — одна HTML-страница (`frontend/index.html`) с формой и списком, обращается к бэкенду через `fetch`. Отдаётся тем же Flask-процессом.
- **База данных** — PostgreSQL, отдельный контейнер (не встроенный SQLite-файл).

## Как запустить

### 1. Поднять базу данных (Postgres в Docker)

```bash
docker run --name lab0-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=lab0 \
  -p 5432:5432 \
  -d postgres:16
```

Проверить, что контейнер поднялся:

```bash
docker ps
```

Должна быть строка с именем `lab0-postgres` и статусом `Up`.

### 2. Установить зависимости бэкенда

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # на Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запустить бэкенд

```bash
python app.py
```

При первом запуске в консоли должно появиться `Подключение к базе установлено`, а
затем Flask сообщит, что сервер поднялся на `http://0.0.0.0:5001`.

(Порт 5001, а не стандартный для Flask 5000 — на macOS порт 5000 обычно занят
системным AirPlay Receiver.)

### 4. Открыть приложение

Перейти в браузере на [http://localhost:5001](http://localhost:5001).

## Проверка работоспособности

1. Открыть [http://localhost:5001](http://localhost:5001) — увидеть форму и (пустой) список.
2. Ввести текст в поле и нажать «Добавить» — заметка появляется в списке.
3. Перезагрузить страницу (F5) — заметка осталась на месте, потому что она реально
   лежит в базе Postgres, а не в памяти браузера или процесса.
4. (Необязательно, но наглядно) Остановить и снова запустить `python app.py` —
   заметки всё равно на месте: они хранятся не в переменных Python, а в БД.

## Остановить всё

```bash
# бэкенд: Ctrl+C в терминале, где запущен python app.py

# база данных:
docker stop lab0-postgres
docker rm lab0-postgres
```

## Структура проекта

```
lab0/
├── backend/
│   ├── app.py            # Flask-приложение + два эндпоинта
│   └── requirements.txt
├── frontend/
│   └── index.html         # форма + список, ходит в /api/notes
└── README.md
```

## Скриншот работающего приложения

<img width="982" height="869" alt="Снимок экрана — 2026-09-17 в 01 03 22" src="https://github.com/user-attachments/assets/f4b54724-222d-46d6-ae39-2275d962e762" />

