
import os
import time
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "lab0")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

app = Flask(__name__, static_folder="../frontend", static_url_path="")


def get_connection():
    
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def wait_for_db_and_init(max_attempts=15, delay_seconds=2):
   
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
        
    ) from last_error


@app.route("/")
def index():
    
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/notes", methods=["GET"])
def list_notes():
    
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC;")
            rows = cur.fetchall()
    finally:
        conn.close()
    
    notes = [
        {"id": r["id"], "text": r["text"], "created_at": r["created_at"].isoformat()}
        for r in rows
    ]
    return jsonify(notes)


@app.route("/api/notes", methods=["POST"])
def create_note():
    
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
    
    app.run(host="0.0.0.0", port=5001, debug=True)
