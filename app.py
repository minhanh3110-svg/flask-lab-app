import sqlite3

def get_db_connection():
    conn = sqlite3.connect("lab_app.db")
    conn.row_factory = sqlite3.Row  # Truy xuất theo tên cột
    return conn
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'abc123'
DB_NAME = 'database.db'

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and "username" not in session:
        return redirect(url_for("login"))

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            employee_id TEXT,
            species TEXT,
            status TEXT,
            action TEXT,
            start_time TEXT,
            end_time TEXT,
            total_hours REAL,
            box INTEGER,
            media TEXT,
            bags_mother INTEGER,
            clusters_mother INTEGER,
            bags_child INTEGER,
            clusters_child INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '123', 'admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('nhanvien', '123', 'nhap')")
    conn.commit()
    conn.close()

def calc_hours(start, end):
    try:
        t1 = datetime.strptime(start, "%H:%M")
        t2 = datetime.strptime(end, "%H:%M")
        return round((t2 - t1).seconds / 3600, 2)
    except:
        return 0

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["username"] = username
            session["role"] = user[0]
            return redirect(url_for("index"))
        flash("Sai tài khoản hoặc mật khẩu")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def index():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    query = "SELECT *, CASE WHEN total_hours > 0 THEN clusters_child * 1.0 / total_hours ELSE 0 END AS productivity FROM logs"
    params = []

    if from_date and to_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [from_date, to_date]

    query += " ORDER BY date DESC"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    logs = c.fetchall()
    conn.close()
    return render_template("index.html", logs=logs)

@app.route("/add_log", methods=["POST"])
def add_log():
    data = request.form
    total_hours = calc_hours(data["start_time"], data["end_time"])
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (date, employee_id, species, status, action, start_time, end_time, total_hours,
                          box, media, bags_mother, clusters_mother, bags_child, clusters_child)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["date"], data["employee_id"], data["species"], data["status"], data["action"],
        data["start_time"], data["end_time"], total_hours,
        data["box"], data["media"], data["bags_mother"], data["clusters_mother"],
        data["bags_child"], data["clusters_child"]
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/edit_log/<int:log_id>", methods=["GET", "POST"])
def edit_log(log_id):
    if session.get("role") != "admin":
        return "Không có quyền", 403

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == "POST":
        data = request.form
        total_hours = calc_hours(data["start_time"], data["end_time"])
        c.execute("""UPDATE logs SET date=?, employee_id=?, species=?, status=?, action=?, 
                     start_time=?, end_time=?, total_hours=?, box=?, media=?, bags_mother=?, 
                     clusters_mother=?, bags_child=?, clusters_child=? WHERE id=?""", (
            data["date"], data["employee_id"], data["species"], data["status"], data["action"],
            data["start_time"], data["end_time"], total_hours, data["box"], data["media"],
            data["bags_mother"], data["clusters_mother"], data["bags_child"], data["clusters_child"], log_id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    c.execute("SELECT * FROM logs WHERE id=?", (log_id,))
    log = c.fetchone()
    conn.close()
    return render_template("edit.html", log=log)

@app.route("/delete_log/<int:log_id>")
def delete_log(log_id):
    if session.get("role") != "admin":
        return "Không có quyền", 403
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/export_excel")
def export_excel():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    conn.close()
    path = "export.xlsx"
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=10000)
