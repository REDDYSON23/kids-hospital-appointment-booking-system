from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

# ---------------- CREATE TABLES ----------------
def create_tables():
    db = get_db()

    # USERS TABLE
    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        password TEXT,
        disease TEXT,
        role TEXT
    )
    """)

    # APPOINTMENTS TABLE
    db.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        doctor_id INTEGER,
        date TEXT,
        time TEXT,
        problem TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    # 🔥 FORCE ADMIN (ALWAYS CORRECT)
    db.execute("DELETE FROM users WHERE email='admin'")
    db.execute("""
    INSERT INTO users (name,email,phone,password,disease,role)
    VALUES ('Admin','admin','0000000000','123456','-','admin')
    """)

    # DOCTORS
    doctors = [
        ("Dr. Chintu 👶 - Pediatrician","chintu"),
        ("Dr. Pinky 🧸 - Child Specialist","pinky"),
        ("Dr. Bunny 🐰 - Kids Surgeon","bunny"),
        ("Dr. Teddy ❤️ - Cardiologist","teddy"),
        ("Dr. Minnie 🎀 - Dermatologist","minnie"),
        ("Dr. Tom 👂 - ENT Specialist","tom"),
        ("Dr. Jerry 🧠 - Neurologist","jerry"),
        ("Dr. Dora 🥗 - Nutritionist","dora"),
        ("Dr. Motu 🦴 - Orthopedic","motu"),
        ("Dr. Patlu 💊 - General Physician","patlu"),
        ("Dr. Hulk 💪 - Physiotherapist","hulk"),
        ("Dr. Barbie 😊 - Psychologist","barbie"),
        ("Dr. Spider 🕷 - Emergency Care","spider")
    ]

    for d in doctors:
        if not db.execute("SELECT * FROM users WHERE email=?", (d[1],)).fetchone():
            db.execute("""
            INSERT INTO users (name,email,phone,password,disease,role)
            VALUES (?,?,?,?,?,?)
            """, (d[0], d[1], "9999999999", "123", "-", "doctor"))

    db.commit()

create_tables()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # 🔥 HARD FIX FOR ADMIN (NO FAILURE)
        if email == "admin" and password == "123456":
            session["user_id"] = 0
            session["name"] = "Admin"
            session["role"] = "admin"
            return redirect("/admin")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        if user:
            session["user_id"] = user[0]
            session["name"] = user[1]
            session["role"] = user[6]

            if user[6] == "doctor":
                return redirect("/doctor_dashboard")
            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = get_db()
        db.execute("""
        INSERT INTO users (name,email,phone,password,disease,role)
        VALUES (?,?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["email"],
            request.form["phone"],
            request.form["password"],
            request.form["disease"],
            "patient"
        ))
        db.commit()
        return redirect("/")

    return render_template("register.html")

# ---------------- PATIENT DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "patient":
        return redirect("/")

    db = get_db()

    appointments = db.execute("""
    SELECT a.id, d.name, a.date, a.time, a.problem, a.status
    FROM appointments a
    JOIN users d ON a.doctor_id = d.id
    WHERE a.user_id=?
    """, (session["user_id"],)).fetchall()

    return render_template("dashboard.html", appointments=appointments)

# ---------------- DOCTORS ----------------
@app.route("/doctors")
def doctors():
    db = get_db()
    doctors = db.execute("SELECT id,name FROM users WHERE role='doctor'").fetchall()
    return render_template("doctors.html", doctors=doctors)

# ---------------- BOOK ----------------
@app.route("/book/<int:id>", methods=["GET","POST"])
def book(id):
    if request.method == "POST":
        db = get_db()
        db.execute("""
        INSERT INTO appointments (user_id,doctor_id,date,time,problem,status)
        VALUES (?,?,?,?,?,?)
        """, (
            session["user_id"],
            id,
            request.form["date"],
            request.form["time"],
            request.form["problem"],
            "Pending"
        ))
        db.commit()
        return redirect("/dashboard")

    return render_template("book.html")

# ---------------- DOCTOR DASHBOARD ----------------
@app.route("/doctor_dashboard")
def doctor_dashboard():
    if session.get("role") != "doctor":
        return redirect("/")

    db = get_db()

    appointments = db.execute("""
    SELECT id, user_id, doctor_id, date, time, problem, status
    FROM appointments
    WHERE doctor_id=?
    """, (session["user_id"],)).fetchall()

    return render_template(
        "doctor_dashboard.html",
        appointments=appointments,
        name=session["name"]
    )

# ---------------- ACCEPT ----------------
@app.route("/accept/<int:id>")
def accept(id):
    db = get_db()
    db.execute("UPDATE appointments SET status='Accepted' WHERE id=?", (id,))
    db.commit()
    return redirect("/doctor_dashboard")

# ---------------- REJECT ----------------
@app.route("/reject/<int:id>")
def reject(id):
    db = get_db()
    db.execute("UPDATE appointments SET status='Rejected' WHERE id=?", (id,))
    db.commit()
    return redirect("/doctor_dashboard")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "❌ Access Denied"

    db = get_db()

    users = db.execute("SELECT * FROM users").fetchall()

    appointments = db.execute("""
    SELECT a.id, u.name, d.name, a.date, a.time, a.problem, a.status
    FROM appointments a
    JOIN users u ON a.user_id = u.id
    JOIN users d ON a.doctor_id = d.id
    """).fetchall()

    return render_template("admin.html", users=users, appointments=appointments)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
