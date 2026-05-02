import sqlite3
from flask import Flask, request, jsonify, g
from flask_cors import CORS

DB_PATH = "students.db"

app = Flask(__name__)
CORS(app)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            group_no  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS grades (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject    TEXT NOT NULL,
            grade      INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


@app.route("/students", methods=["GET"])
def list_students():
    rows = get_db().execute("SELECT * FROM students ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/students", methods=["POST"])
def create_student():
    data = request.get_json()
    db = get_db()
    cur = db.execute(
        "INSERT INTO students (name, group_no) VALUES (?, ?)",
        (data["name"], data["group_no"]),
    )
    db.commit()
    new_id = cur.lastrowid
    row = db.execute("SELECT * FROM students WHERE id = ?", (new_id,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json()
    db = get_db()
    db.execute(
        "UPDATE students SET name = ?, group_no = ? WHERE id = ?",
        (data["name"], data["group_no"], student_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return "", 204


@app.route("/students/<int:student_id>/grades", methods=["GET"])
def list_grades(student_id):
    rows = get_db().execute(
        "SELECT * FROM grades WHERE student_id = ? ORDER BY id",
        (student_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/grades", methods=["POST"])
def create_grade():
    data = request.get_json()
    db = get_db()
    cur = db.execute(
        "INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)",
        (data["student_id"], data["subject"], data["grade"]),
    )
    db.commit()
    new_id = cur.lastrowid
    row = db.execute("SELECT * FROM grades WHERE id = ?", (new_id,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/grades/<int:grade_id>", methods=["PUT"])
def update_grade(grade_id):
    data = request.get_json()
    db = get_db()
    db.execute(
        "UPDATE grades SET subject = ?, grade = ? WHERE id = ?",
        (data["subject"], data["grade"], grade_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM grades WHERE id = ?", (grade_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.route("/grades/<int:grade_id>", methods=["DELETE"])
def delete_grade(grade_id):
    db = get_db()
    db.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
    db.commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
