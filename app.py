import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect("lab_app.db")
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = "secret-key-123"

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and "username" not in session:
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/")
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = {
            "date": request.form["date"],
            "staff": session["username"],
            "variety": request.form["variety"],
            "status": request.form["status"],
            "action": request.form["action"],
            "start_time": request.form["start_time"],
            "end_time": request.form["end_time"],
            "box": request.form["box"],
            "medium": request.form["medium"],
            "mother_bag": request.form["mother_bag"],
            "cluster_per_mother": request.form["cluster_per_mother"],
            "child_bag": request.form["child_bag"],
            "cluster_per_child": request.form["cluster_per_child"]
        }
        try:
            fmt = "%H:%M"
            start = datetime.strptime(data["start_time"], fmt)
            end = datetime.strptime(data["end_time"], fmt)
            hours = (end - start).seconds / 3600
        except:
            hours = 0
        total_clusters = int(data["child_bag"]) * int(data["cluster_per_child"])
        productivity = round(total_clusters / hours, 2) if hours > 0 else 0

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO log_entries (
                date, staff, variety, status, action, start_time, end_time, box,
                medium, mother_bag, cluster_per_mother, child_bag, cluster_per_child,
                total_hours, productivity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["date"], data["staff"], data["variety"], data["status"], data["action"],
            data["start_time"], data["end_time"], data["box"], data["medium"],
            data["mother_bag"], data["cluster_per_mother"], data["child_bag"], data["cluster_per_child"],
            hours, productivity
        ))
        conn.commit()
        conn.close()
        flash("Đã lưu nhật ký!")
        return redirect(url_for("index"))

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
    @app.route("/edit/<int:log_id>", methods=["GET", "POST"])
def edit_log(log_id):
    if session.get("role") != "admin":
        return "Không có quyền truy cập", 403

    conn = get_db_connection()

    if request.method == "POST":
        data = request.form
        try:
            fmt = "%H:%M"
            start = datetime.strptime(data["start_time"], fmt)
            end = datetime.strptime(data["end_time"], fmt)
            hours = (end - start).seconds / 3600
        except:
            hours = 0

        total_clusters = int(data["child_bag"]) * int(data["cluster_per_child"])
        productivity = round(total_clusters / hours, 2) if hours > 0 else 0

        conn.execute("""
            UPDATE log_entries SET
                date=?, staff=?, variety=?, status=?, action=?, start_time=?, end_time=?,
                box=?, medium=?, mother_bag=?, cluster_per_mother=?, child_bag=?, cluster_per_child=?,
                total_hours=?, productivity=?
            WHERE id=?
        """, (
            data["date"], data["staff"], data["variety"], data["status"], data["action"],
            data["start_time"], data["end_time"], data["box"], data["medium"],
            data["mother_bag"], data["cluster_per_mother"], data["child_bag"], data["cluster_per_child"],
            hours, productivity, log_id
        ))
        conn.commit()
        conn.close()
        return redirect("/logs")

    log = conn.execute("SELECT * FROM log_entries WHERE id=?", (log_id,)).fetchone()
    conn.close()
    return render_template("edit.html", log=log)
