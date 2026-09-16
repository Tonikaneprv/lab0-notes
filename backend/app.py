"""
Лаба 0 — свой сервис.

Простое приложение "Заметки":
- фронтенд (папка ../frontend) отдаётся этим же процессом Flask
- бэкенд даёт два эндпоинта:
    GET  /api/notes  -> вернуть все заметки из базы
    POST /api/notes  -> сохранить новую заметку в базу
- база данных — PostgreSQL, отдельный сетевой сервис (поднимается через Docker,
  см. README.md), а не встроенный SQLite-файл.

Как это доказывает, что данные реально лежат в базе, а не в памяти процесса:
если перезапустить сам процесс app.py (не трогая контейнер с Postgres),
заметки никуда не денутся — они лежат не в переменных Python, а в БД.
"""

import os
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory

# --- настройки подключения к базе ---
# Значения по умолчанию совпадают с командой docker run из README.md.
# В реальном проекте такие вещи обычно не хардкодят, а берут из переменных
# окружения — мы здесь так и делаем, чтобы было легко поменять хост/пароль,
# не трогая код (это же пригодится в следующих лабах с Docker Compose).
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "lab0")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

app = Flask(__name__, static_folder="../frontend", static_url_path="")


def get_connection():
    """Открыть новое соединение с Postgres."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def wait_for_db_and_init(max_attempts=15, delay_seconds=2):
    """
    Подождать, пока поднимется контейнер с Postgres, и создать таблицу notes,
    если её ещё нет. Ретраи нужны потому, что docker run для контейнера с
    базой и запуск python app.py — два независимых процесса: если база ещё
    не успела стартовать, первое подключение может упасть с ошибкой.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            conn = get_connection()
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                    """
                )
            conn.close()
            print(f"[app] Подключение к базе установлено (попытка {attempt}).")
            return
        except psycopg2.OperationalError as exc:
            last_error = exc
            print(
                f"[app] База пока недоступна (попытка {attempt}/{max_attempts}): {exc}"
            )
            time.sleep(delay_seconds)
    raise RuntimeError(
        "Не удалось подключиться к Postgres. Проверьте, что контейнер запущен "
        "(docker ps) и переменные окружения указывают на правильный хост/порт."
    ) from last_error


@app.route("/")
def index():
    """Отдать главную страницу фронтенда."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/notes", methods=["GET"])
def list_notes():
    """Прочитать все заметки из базы, самые новые — первыми."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC;")
            rows = cur.fetchall()
    finally:
        conn.close()
    # created_at приходит как datetime — приводим к строке, чтобы jsonify не ругался
    notes = [
        {"id": r["id"], "text": r["text"], "created_at": r["created_at"].isoformat()}
        for r in rows
    ]
    return jsonify(notes)


@app.route("/api/notes", methods=["POST"])
def create_note():
    """Записать новую заметку в базу."""
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Поле 'text' обязательно и не может быть пустым"}), 400

    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO notes (text) VALUES (%s) RETURNING id, text, created_at;",
                (text,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    note = {"id": row["id"], "text": row["text"], "created_at": row["created_at"].isoformat()}
    return jsonify(note), 201


if __name__ == "__main__":
    wait_for_db_and_init()
    # порт 5000 на macOS часто занят системным AirPlay Receiver, поэтому берём 5001
    app.run(host="0.0.0.0", port=5001, debug=True)
