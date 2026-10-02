import os
import re
import sqlite3
import random
import hashlib
from datetime import datetime, timedelta
from io import BytesIO

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, url_for, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DB_PATH = os.path.join(BASE_DIR, "skillshare.db")

app = Flask(__name__)
app.secret_key = os.getenv("SKILLSHARE_SECRET_KEY", "skillshare_secret_key_2026_change_me")

# Optional real SMS OTP configuration.
# Set these environment variables to enable real Indian SMS OTP delivery:
# FAST2SMS_API_KEY=your_api_key
# FAST2SMS_OTP_ID=your_otp_template_id
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "").strip()
FAST2SMS_OTP_ID = os.getenv("FAST2SMS_OTP_ID", "").strip()
OTP_MINUTES = 10

COURSE_SEEDS = [
    ("Python Masterclass", "Build real-world Python applications from the ground up.", "PY", "Programming", "Beginner", "18h 30m", 4.9, 12500, "https://www.youtube.com/watch?v=rfscVS0vtbw", "blue", 12, 1),
    ("HTML & CSS", "Create beautiful, responsive websites with modern HTML and CSS.", "</>", "Web Development", "Beginner", "12h 15m", 4.8, 9800, "https://www.youtube.com/watch?v=916GWv2Qs08", "purple", 10, 1),
    ("Flask Development", "Develop powerful Python web applications with Flask, Jinja and SQLite.", "FL", "Backend", "Intermediate", "15h 45m", 4.9, 8100, "https://www.youtube.com/watch?v=Qr4QMBUPxWo", "teal", 11, 1),
    ("Artificial Intelligence", "Understand AI, machine learning and deep learning with practical concepts.", "AI", "AI / ML", "Intermediate", "20h 10m", 4.8, 7600, "https://www.youtube.com/watch?v=JMUxmLyrhSk", "pink", 14, 0),
    ("JavaScript Pro", "Master modern JavaScript and build interactive web experiences.", "JS", "Web Development", "Intermediate", "16h 20m", 4.9, 11200, "https://www.youtube.com/watch?v=PkZNo7MFNFg", "orange", 13, 1),
    ("SQL Database", "Learn SQL, joins, queries and database design with practical examples.", "SQL", "Database", "Beginner", "10h 40m", 4.8, 6700, "https://www.youtube.com/watch?v=HXV3zeQKqGY", "gold", 9, 0),
]


# Course-specific final assessments: 20 MCQs per course.
TESTS = {
    1: [
        ("Which keyword defines a function in Python?", ["func", "def", "function", "lambda"], 1),
        ("Which type is used for whole numbers?", ["float", "int", "str", "bool"], 1),
        ("What does len() return?", ["Memory size", "Number of items", "Data type", "Last index"], 1),
        ("Which collection is ordered and mutable?", ["tuple", "set", "list", "frozenset"], 2),
        ("What symbol starts a Python comment?", ["//", "#", "--", "/*"], 1),
        ("Which statement handles exceptions?", ["try/except", "if/error", "catch/throw", "error/handle"], 0),
        ("What is the output type of input()?", ["int", "float", "str", "bool"], 2),
        ("Which loop is commonly used to iterate over a sequence?", ["for", "switch", "repeat", "case"], 0),
        ("What does a dictionary store?", ["Only indexes", "Key-value pairs", "Only values", "Binary trees"], 1),
        ("Which operator checks equality?", ["=", "!=", "==", ":="], 2),
        ("What is PEP 8?", ["A database", "Python style guide", "A compiler", "A package manager"], 1),
        ("Which keyword creates a class?", ["object", "struct", "class", "type"], 2),
        ("What does import do?", ["Deletes a module", "Loads a module", "Runs SQL", "Creates a variable only"], 1),
        ("Which is immutable?", ["list", "dict", "set", "tuple"], 3),
        ("What does range(5) produce?", ["1 to 5", "0 to 4", "0 to 5", "5 to 10"], 1),
        ("Which keyword returns a value from a function?", ["yield", "return", "send", "break"], 1),
        ("What is a virtual environment used for?", ["Isolating project dependencies", "Editing images", "Hosting DNS", "Compressing files"], 0),
        ("Which library is widely used for data analysis?", ["Pandas", "Flask", "Jinja", "Requests only"], 0),
        ("What does pip primarily manage?", ["Python packages", "HTML tags", "SQL tables", "Windows drivers"], 0),
        ("Which value represents Boolean true?", ["true", "TRUE", "True", "1.0"], 2),
    ],
    2: [
        ("Which tag creates the main heading?", ["<h6>", "<head>", "<h1>", "<title>"], 2),
        ("Which tag creates a hyperlink?", ["<a>", "<link>", "<href>", "<url>"], 0),
        ("Which attribute provides an image URL?", ["href", "src", "alt", "path"], 1),
        ("Which tag creates an unordered list?", ["<ol>", "<ul>", "<li>", "<list>"], 1),
        ("Which CSS property changes text color?", ["font-color", "text-color", "color", "foreground"], 2),
        ("Which CSS layout system is one-dimensional?", ["Grid", "Flexbox", "Float", "Position"], 1),
        ("Which unit is relative to the root font size?", ["px", "em", "rem", "%"], 2),
        ("Which selector targets a class?", ["#card", ".card", "card", "*card"], 1),
        ("Which selector targets an id?", [".hero", "#hero", "hero", "@hero"], 1),
        ("What does box-sizing: border-box do?", ["Adds shadow", "Includes padding/border in declared size", "Centers a box", "Hides overflow"], 1),
        ("Which HTML element is semantic for navigation?", ["<nav>", "<menuitem>", "<navigate>", "<links>"], 0),
        ("Which tag embeds a video?", ["<media>", "<movie>", "<video>", "<embedvideo>"], 2),
        ("Which CSS property controls spacing inside an element?", ["margin", "padding", "gap-out", "space"], 1),
        ("What does display: grid create?", ["A grid layout", "A database", "An image", "A font"], 0),
        ("Which meta setting helps responsive layouts?", ["viewport", "charset-only", "author", "robots"], 0),
        ("What does alt text improve?", ["Database speed", "Image accessibility", "CSS animation", "Server memory"], 1),
        ("Which pseudo-class applies when hovering?", [":focus", ":active", ":hover", ":visited-only"], 2),
        ("Which property rounds corners?", ["corner-radius", "border-radius", "round", "radius-border"], 1),
        ("Which HTML tag defines a paragraph?", ["<text>", "<para>", "<p>", "<paragraph>"], 2),
        ("Which CSS property controls stacking order?", ["stack", "z-index", "layer", "order-index"], 1),
    ],
    3: [
        ("Which function creates a Flask application?", ["Flask(__name__)", "App()", "create_flask()", "Flask.start()"], 0),
        ("Which decorator defines a route?", ["@app.route", "@route.app", "@url", "@flask.path"], 0),
        ("Which template engine does Flask commonly use?", ["Twig", "Jinja2", "Blade", "EJS"], 1),
        ("Which method reads form data in Flask?", ["request.form", "form.data()", "request.input", "flask.formdata"], 0),
        ("Which function renders an HTML template?", ["render_page", "render_template", "template", "show_html"], 1),
        ("Which database is used by this SkillShare build?", ["MongoDB", "SQLite", "Oracle", "Redis"], 1),
        ("What does app.run() do?", ["Starts the development server", "Creates a database", "Compiles CSS", "Installs Flask"], 0),
        ("Which object stores per-user session data?", ["session", "cookiejar", "state", "userbag"], 0),
        ("What protects a Flask app's session cookie?", ["SECRET_KEY", "PORT", "DEBUG", "HOST"], 0),
        ("Which HTTP method is commonly used for form submission that changes data?", ["GET", "POST", "TRACE", "HEAD"], 1),
        ("Which helper generates a URL for an endpoint?", ["url_for", "make_url", "route_for", "href_for"], 0),
        ("What is Jinja syntax for a variable?", ["{{ value }}", "[[ value ]]", "<% value %>", "(( value ))"], 0),
        ("What is Jinja syntax for a control block?", ["{{ }}", "{% %}", "[[ ]]", "<% %>"], 1),
        ("Which file commonly stores Flask routes in this project?", ["app.py", "index.css", "main.sql", "server.json"], 0),
        ("What does redirect() do?", ["Sends the client to another URL", "Deletes a user", "Stops Python", "Creates a template"], 0),
        ("Which decorator restricts a route to POST?", ["@app.post", "@app.onlypost", "@post.route", "@request.postonly"], 0),
        ("What is a blueprint used for?", ["Organizing Flask application components", "Editing videos", "Creating SQL indexes only", "Hashing passwords"], 0),
        ("Which library is used for password hashing here?", ["Werkzeug", "Pillow", "NumPy", "Matplotlib"], 0),
        ("Why use parameterized SQL?", ["To reduce SQL injection risk", "To increase font size", "To create CSS", "To embed YouTube"], 0),
        ("What does sqlite3.Row provide?", ["Column access by name", "Automatic encryption", "HTML rendering", "Video streaming"], 0),
    ],
    4: [
        ("What does AI stand for?", ["Automated Internet", "Artificial Intelligence", "Applied Interface", "Algorithmic Input"], 1),
        ("What is supervised learning trained with?", ["Labeled data", "No data", "Only images", "Random passwords"], 0),
        ("What is a feature?", ["An input variable used by a model", "A server", "A certificate", "A database table only"], 0),
        ("What is classification?", ["Predicting categories", "Compressing files", "Sorting code alphabetically", "Rendering HTML"], 0),
        ("What is regression?", ["Predicting continuous values", "Deleting rows", "Creating routes", "Styling pages"], 0),
        ("What does overfitting mean?", ["Model fits training data too closely", "Model has no parameters", "Data is encrypted", "Training is skipped"], 0),
        ("What is a training set?", ["Data used to learn model parameters", "Final certificate", "Database backup", "Web page"], 0),
        ("Why use a validation set?", ["To tune/check model performance during development", "To store passwords", "To create CSS", "To send OTP"], 0),
        ("Which metric is common for classification?", ["Accuracy", "Pixel density", "CPU clock", "Page height"], 0),
        ("What is a neural network inspired by?", ["Biological neural systems", "SQL joins", "HTML tags", "File folders"], 0),
        ("What is an epoch?", ["One full pass through training data", "One database row", "One HTTP request", "One CSS rule"], 0),
        ("What does a learning rate control?", ["Step size of parameter updates", "Screen brightness", "Database size", "Video quality"], 0),
        ("What is deep learning?", ["Learning with multi-layer neural networks", "A long HTML page", "A database backup", "A CSS framework"], 0),
        ("What is inference?", ["Using a trained model to produce predictions", "Training from scratch", "Deleting training data", "Writing HTML"], 0),
        ("What is an unlabeled dataset?", ["Data without target labels", "Data with every answer", "Only numeric data", "Encrypted data"], 0),
        ("Why normalize features?", ["Put values on comparable scales", "Delete outliers always", "Create HTML", "Increase file size"], 0),
        ("What is a confusion matrix?", ["A table of classification outcomes", "A neural network", "A SQL query", "A Flask route"], 0),
        ("What is generative AI designed to do?", ["Generate new content", "Only sort numbers", "Only store data", "Only render CSS"], 0),
        ("What is a model parameter?", ["A value learned/optimized by a model", "A browser tab", "A database password", "A file extension"], 0),
        ("Why split data into train and test sets?", ["To evaluate generalization on unseen data", "To make CSS responsive", "To send OTP", "To compress images"], 0),
    ],
    5: [
        ("Which keyword declares a block-scoped variable that can be reassigned?", ["var", "let", "const", "static"], 1),
        ("Which keyword declares a constant binding?", ["let", "var", "const", "fixed"], 2),
        ("Which method converts JSON text into an object?", ["JSON.parse", "JSON.read", "JSON.object", "parse.JSON"], 0),
        ("Which method converts an object into JSON text?", ["JSON.stringify", "JSON.text", "JSON.encodeOnly", "toJSONText"], 0),
        ("What does === compare?", ["Value and type", "Only value", "Only type", "References only"], 0),
        ("Which array method adds to the end?", ["shift", "push", "pop", "unshift"], 1),
        ("Which array method removes the last item?", ["push", "shift", "pop", "slice"], 2),
        ("What does addEventListener do?", ["Registers an event handler", "Adds CSS", "Creates SQL", "Starts Flask"], 0),
        ("Which event fires when a button is clicked?", ["hover", "click", "press", "tap-only"], 1),
        ("What does document.querySelector return?", ["First matching element", "All pages", "A database", "A URL"], 0),
        ("Which operator means logical AND?", ["||", "&&", "!!", "and()"], 1),
        ("Which operator means logical OR?", ["&&", "||", "??!", "or()"], 1),
        ("What is an arrow function?", ["A concise function syntax", "A CSS selector", "A database query", "A browser extension"], 0),
        ("Which method creates a new array by transforming items?", ["map", "join", "findIndex", "sortOnly"], 0),
        ("Which method filters an array?", ["filter", "reduceOnly", "select", "whereJS"], 0),
        ("What does localStorage store?", ["Key-value data in the browser", "Server files", "SQL tables", "Python objects"], 0),
        ("What does fetch() commonly do?", ["Makes network requests", "Compiles CSS", "Creates a class", "Opens SQLite"], 0),
        ("What is the DOM?", ["Document Object Model", "Data Output Method", "Digital Object Memory", "Document Order Map"], 0),
        ("Which value represents no assigned value?", ["undefined", "empty-only", "voided", "nil"], 0),
        ("Which keyword handles asynchronous waiting?", ["await", "pause", "waitfor", "hold"], 0),
    ],
    6: [
        ("Which SQL command reads data?", ["SELECT", "READ", "FETCHROW", "OPEN"], 0),
        ("Which clause filters rows?", ["WHERE", "FILTER", "HAVINGONLY", "LIMITBY"], 0),
        ("Which clause sorts results?", ["ORDER BY", "SORT", "GROUP SORT", "ARRANGE"], 0),
        ("Which command adds rows?", ["INSERT", "ADDROW", "APPENDSQL", "CREATE ROW"], 0),
        ("Which command changes existing rows?", ["UPDATE", "ALTER ROW", "CHANGE", "MODIFY ONLY"], 0),
        ("Which command removes rows?", ["DELETE", "REMOVE ROW", "DROP ROWS ONLY", "CLEAR"], 0),
        ("What is a primary key?", ["Unique identifier for a row", "A password", "A view", "A query"], 0),
        ("What does a foreign key represent?", ["A relationship to another table's key", "A duplicate password", "A stored procedure", "A CSS key"], 0),
        ("Which join returns matching rows from both tables?", ["INNER JOIN", "ONLY JOIN", "MATCH JOIN", "PAIR JOIN"], 0),
        ("Which function counts rows?", ["COUNT", "TOTALROWS", "NUMBEROF", "ROWS"], 0),
        ("Which clause groups rows for aggregates?", ["GROUP BY", "CLUSTER BY", "PACK BY", "COLLECT BY"], 0),
        ("Which clause filters grouped results?", ["HAVING", "WHERE GROUP", "AFTER", "FILTER GROUP"], 0),
        ("What does DISTINCT do?", ["Removes duplicate result values", "Deletes rows", "Encrypts data", "Creates a table"], 0),
        ("Which command creates a table?", ["CREATE TABLE", "MAKE TABLE", "NEW TABLE", "TABLE CREATE ONLY"], 0),
        ("Which constraint prevents duplicate values?", ["UNIQUE", "NO-DUP", "DISTINCT-KEY", "SINGLE"], 0),
        ("What does NOT NULL enforce?", ["A value must be present", "A value must be unique", "A row must be deleted", "A table must be empty"], 0),
        ("What is normalization mainly used for?", ["Reducing redundant data and anomalies", "Increasing duplication", "Rendering pages", "Sending OTP"], 0),
        ("Which command changes table structure?", ["ALTER TABLE", "CHANGE TABLE", "EDIT TABLE", "UPDATE STRUCTURE"], 0),
        ("What is an index used for?", ["Improving lookup/query performance", "Storing passwords only", "Rendering CSS", "Generating PDFs"], 0),
        ("Which transaction command makes changes permanent?", ["COMMIT", "SAVE NOW", "FINALIZE", "APPLY"], 0),
    ],
}


def certificate_tier(score):
    score = int(score or 0)
    if score >= 90:
        return "DIAMOND", "diamond"
    if score >= 75:
        return "GOLD", "gold"
    if score >= 50:
        return "PLATINUM", "platinum"
    return "NO CERTIFICATE", "none"


def certificate_id(user_id, course_id, attempt_id):
    return f"SS-{datetime.now().strftime('%Y')}-{int(course_id):02d}-{int(user_id):04d}-{int(attempt_id):05d}"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_exists(conn, table, column):
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def add_column(conn, table, column, definition):
    if not column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def normalize_phone(phone):
    return re.sub(r"\D", "", phone or "")


def valid_phone(phone):
    return bool(re.fullmatch(r"[6-9]\d{9}", phone or ""))


def is_password_hash(value):
    return isinstance(value, str) and value.startswith(("scrypt:", "pbkdf2:", "argon2:"))


def verify_password(stored, entered):
    if is_password_hash(stored):
        try:
            return check_password_hash(stored, entered)
        except Exception:
            return False
    return stored == entered


def upgrade_password(conn, table, row_id, password):
    conn.execute(f"UPDATE {table} SET password=? WHERE id=?", (generate_password_hash(password), row_id))


def youtube_id(url):
    url = (url or "").strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/", 1)[1].split("?", 1)[0].split("&", 1)[0]
    if "youtube.com/watch" in url and "v=" in url:
        return url.split("v=", 1)[1].split("&", 1)[0]
    if "youtube.com/embed/" in url:
        return url.split("embed/", 1)[1].split("?", 1)[0].split("&", 1)[0]
    return ""


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage INTEGER NOT NULL,
            tier TEXT NOT NULL,
            taken_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS connections(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_a, user_b),
            CHECK(user_a < user_b),
            FOREIGN KEY(user_a) REFERENCES users(id),
            FOREIGN KEY(user_b) REFERENCES users(id)
        )
    """)

    add_column(conn, "users", "phone", "TEXT DEFAULT ''")
    add_column(conn, "users", "phone_verified", "INTEGER DEFAULT 0")
    add_column(conn, "users", "created_at", "TEXT")

    for name, definition in {
        "category": "TEXT DEFAULT 'Technology'", "level": "TEXT DEFAULT 'Beginner'",
        "duration": "TEXT DEFAULT '8h 30m'", "rating": "REAL DEFAULT 4.8",
        "students": "INTEGER DEFAULT 1200", "video_url": "TEXT DEFAULT ''",
        "accent": "TEXT DEFAULT 'blue'", "lessons": "INTEGER DEFAULT 12", "featured": "INTEGER DEFAULT 0",
    }.items():
        add_column(conn, "courses", name, definition)

    add_column(conn, "enrollments", "progress", "INTEGER DEFAULT 0")
    add_column(conn, "enrollments", "completed_at", "TEXT")
    add_column(conn, "admins", "phone", "TEXT DEFAULT '9876543210'")
    add_column(conn, "admins", "phone_verified", "INTEGER DEFAULT 0")

    cur.execute("SELECT COUNT(*) FROM courses")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO courses(title,description,icon,category,level,duration,rating,students,video_url,accent,lessons,featured)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, COURSE_SEEDS)
    else:
        for row in COURSE_SEEDS:
            cur.execute("""
                UPDATE courses SET description=?, icon=?, category=?, level=?, duration=?, rating=?, students=?, video_url=?, accent=?, lessons=?, featured=?
                WHERE title=?
            """, (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[0]))

    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admins(email,password,name,phone,phone_verified) VALUES(?,?,?,?,?)",
                    ("admin@skillshare.com", generate_password_hash("admin123"), "SkillShare Admin", "9876543210", 0))
    else:
        admin = cur.execute("SELECT id,password FROM admins ORDER BY id LIMIT 1").fetchone()
        if admin and not is_password_hash(admin["password"]):
            upgrade_password(conn, "admins", admin["id"], admin["password"])

    cur.execute("UPDATE users SET created_at=COALESCE(created_at, datetime('now'))")
    conn.commit()
    conn.close()


init_db()


def user_logged_in():
    return "user_id" in session


def admin_logged_in():
    return bool(session.get("is_admin"))


def user_enrolled_ids(user_id):
    conn = get_db()
    rows = conn.execute("SELECT course_id FROM enrollments WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return {r["course_id"] for r in rows}


def connection_pair(a, b):
    a, b = int(a), int(b)
    return (a, b) if a < b else (b, a)


def is_connected(a, b, conn=None):
    own = conn is None
    conn = conn or get_db()
    x, y = connection_pair(a, b)
    row = conn.execute("SELECT 1 FROM connections WHERE user_a=? AND user_b=?", (x, y)).fetchone()
    if own:
        conn.close()
    return bool(row)


def course_visual_id(course_id):
    return ((int(course_id) - 1) % 6) + 1


def otp_hash(code):
    return hashlib.sha256(str(code).encode()).hexdigest()


def send_sms_otp(phone):
    """Real OTP through Fast2SMS when credentials are configured; otherwise demo OTP is printed to terminal."""
    phone = normalize_phone(phone)
    if FAST2SMS_API_KEY and FAST2SMS_OTP_ID:
        try:
            response = requests.post(
                "https://www.fast2sms.com/dev/otp/send",
                headers={"Authorization": FAST2SMS_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
                json={"otp_id": FAST2SMS_OTP_ID, "mobile": phone, "otp_expiry": OTP_MINUTES, "otp_length": 6},
                timeout=15,
            )
            data = response.json()
            if response.ok and data.get("return"):
                return True, "OTP sent to your mobile number."
            return False, data.get("message", "SMS OTP service rejected the request.")
        except Exception as exc:
            return False, f"SMS service unavailable: {exc}"

    code = f"{random.randint(0, 999999):06d}"
    session["demo_otp_hash"] = otp_hash(code)
    session["demo_otp_expires"] = (datetime.utcnow() + timedelta(minutes=OTP_MINUTES)).isoformat()
    print(f"\n[SkillShare DEMO OTP] +91 {phone} -> {code} (valid for {OTP_MINUTES} minutes)\n")
    return True, "Demo mode: OTP generated in the Flask terminal. Add Fast2SMS credentials for real SMS delivery."


def verify_sms_otp(phone, code):
    phone = normalize_phone(phone)
    if FAST2SMS_API_KEY and FAST2SMS_OTP_ID:
        try:
            response = requests.post(
                "https://www.fast2sms.com/dev/otp/verify",
                headers={"Authorization": FAST2SMS_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
                json={"mobile": phone, "otp": str(code).strip()}, timeout=15,
            )
            data = response.json()
            return response.ok and bool(data.get("return")), data.get("message", "Invalid or expired OTP.")
        except Exception as exc:
            return False, f"SMS service unavailable: {exc}"

    saved = session.get("demo_otp_hash")
    expires = session.get("demo_otp_expires", "")
    if not saved or not expires:
        return False, "OTP expired. Please request a new OTP."
    try:
        if datetime.utcnow() > datetime.fromisoformat(expires):
            session.pop("demo_otp_hash", None); session.pop("demo_otp_expires", None)
            return False, "OTP expired. Please request a new OTP."
    except ValueError:
        return False, "Please request a new OTP."
    ok = saved == otp_hash(code)
    if ok:
        session.pop("demo_otp_hash", None); session.pop("demo_otp_expires", None)
        return True, "OTP verified successfully."
    return False, "Incorrect OTP. Please try again."


@app.context_processor
def global_data():
    return {
        "logged_in": user_logged_in(), "current_user": session.get("fullname", "Learner"),
        "current_phone": session.get("phone", ""), "admin_logged_in": admin_logged_in(),
        "admin_name": session.get("admin_name", "Administrator"),
    }


@app.route("/")
def home():
    conn = get_db()
    featured = conn.execute("SELECT * FROM courses ORDER BY featured DESC, rating DESC LIMIT 6").fetchall()
    conn.close()
    return render_template("index.html", featured=featured)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not fullname or not phone or not email or not password:
            return render_template("register.html", error="Please fill every required field.")
        if not valid_phone(phone):
            return render_template("register.html", error="Enter a valid 10-digit Indian mobile number.")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")
        if len(password) < 6:
            return render_template("register.html", error="Password must contain at least 6 characters.")
        conn = get_db()
        if conn.execute("SELECT id FROM users WHERE phone=?", (phone,)).fetchone():
            conn.close(); return render_template("register.html", error="That mobile number is already registered.")
        if conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            conn.close(); return render_template("register.html", error="That email is already registered.")
        conn.close()
        session["pending_registration"] = {"fullname": fullname, "phone": phone, "email": email, "password_hash": generate_password_hash(password)}
        ok, message = send_sms_otp(phone)
        if not ok:
            session.pop("pending_registration", None)
            return render_template("register.html", error=message)
        return redirect(url_for("verify_registration"))
    return render_template("register.html")


@app.route("/verify-registration", methods=["GET", "POST"])
def verify_registration():
    pending = session.get("pending_registration")
    if not pending:
        return redirect(url_for("register"))
    if request.method == "POST":
        code = request.form.get("otp", "").strip()
        ok, message = verify_sms_otp(pending["phone"], code)
        if not ok:
            return render_template("verify_otp.html", title="Verify your mobile", phone=pending["phone"], error=message, resend_url=url_for("resend_registration_otp"))
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(fullname,email,phone,password,phone_verified,created_at) VALUES(?,?,?,?,?,?)",
                         (pending["fullname"], pending["email"], pending["phone"], pending["password_hash"], 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close(); session.pop("pending_registration", None)
            return render_template("register.html", error="This account already exists. Please login.")
        conn.close()
        session.pop("pending_registration", None)
        flash("Mobile verified. Your SkillShare account is ready.")
        return redirect(url_for("login"))
    return render_template("verify_otp.html", title="Verify your mobile", phone=pending["phone"], resend_url=url_for("resend_registration_otp"))


@app.route("/resend-registration-otp", methods=["GET", "POST"])
def resend_registration_otp():
    pending = session.get("pending_registration")
    if not pending:
        return redirect(url_for("register"))
    ok, message = send_sms_otp(pending["phone"])
    return render_template("verify_otp.html", title="Verify your mobile", phone=pending["phone"], success=message if ok else None, error=None if ok else message, resend_url=url_for("resend_registration_otp"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        phone = normalize_phone(identifier)
        conn = get_db()

        # New accounts use mobile-number login. For older project databases that
        # were created before the mobile/OTP update, also accept the registered
        # email so existing demo accounts are not locked out.
        user = None
        if valid_phone(phone):
            user = conn.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if user is None and "@" in identifier:
            user = conn.execute("SELECT * FROM users WHERE lower(email)=?", (identifier.lower(),)).fetchone()

        if user and verify_password(user["password"], password):
            if not is_password_hash(user["password"]):
                upgrade_password(conn, "users", user["id"], password)
                conn.commit()
            session.clear()
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            session["email"] = user["email"]
            session["phone"] = user["phone"] or ""
            conn.close()
            return redirect(url_for("dashboard"))

        conn.close()
        return render_template("login.html", error="Invalid mobile/email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))


@app.route("/discover")
def discover():
    conn = get_db(); courses = conn.execute("SELECT * FROM courses ORDER BY featured DESC, id ASC").fetchall(); conn.close()
    enrolled = user_enrolled_ids(session["user_id"]) if user_logged_in() else set()
    return render_template("discover.html", courses=courses, enrolled=enrolled)


@app.route("/dashboard")
def dashboard():
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db()
    enrolled = conn.execute("SELECT e.*,c.title,c.description,c.icon,c.category,c.duration,c.rating,c.accent,c.lessons,c.video_url FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=? ORDER BY e.enrolled_at DESC", (session["user_id"],)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    completed = sum(1 for e in enrolled if (e["progress"] or 0) >= 100)
    avg = round(sum((e["progress"] or 0) for e in enrolled)/len(enrolled)) if enrolled else 0
    conn.close(); return render_template("dashboard.html", enrolled=enrolled, total_courses=total, completed=completed, avg_progress=avg)


@app.route("/learning-journey")
def learning_journey():
    if not user_logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("""SELECT c.*, e.progress, e.enrolled_at, e.completed_at
        FROM enrollments e JOIN courses c ON c.id=e.course_id
        WHERE e.user_id=? ORDER BY COALESCE(e.completed_at, e.enrolled_at) DESC""", (session["user_id"],)).fetchall()
    completed = [r for r in rows if (r["progress"] or 0) >= 100]
    active = [r for r in rows if 0 < (r["progress"] or 0) < 100]
    avg = round(sum((r["progress"] or 0) for r in rows) / len(rows)) if rows else 0
    skills = []
    for r in completed:
        label = r["title"].replace(" Masterclass", "").replace(" Development", "").replace(" Database", "")
        if label not in skills:
            skills.append(label)
    categories = {}
    for r in rows:
        categories[r["category"]] = categories.get(r["category"], 0) + 1
    total_lessons = sum(r["lessons"] for r in rows)
    done_lessons = round(sum((r["lessons"] * (r["progress"] or 0) / 100) for r in rows))
    conn.close()
    return render_template("learning_journey.html", courses=rows, completed=completed, active=active, avg_progress=avg, skills=skills, categories=categories, total_lessons=total_lessons, done_lessons=done_lessons)


@app.route("/learner/<int:user_id>")
def learner_profile(user_id):
    if not user_logged_in():
        return redirect(url_for("login"))
    if user_id == session["user_id"]:
        return redirect(url_for("profile"))
    conn = get_db()
    learner = conn.execute("SELECT id, fullname, created_at FROM users WHERE id=?", (user_id,)).fetchone()
    if not learner:
        conn.close()
        return redirect(url_for("community"))
    courses = conn.execute("""SELECT c.*, e.progress, e.completed_at, e.enrolled_at
        FROM enrollments e JOIN courses c ON c.id=e.course_id
        WHERE e.user_id=? ORDER BY e.progress DESC, e.enrolled_at DESC""", (user_id,)).fetchall()
    completed = [c for c in courses if (c["progress"] or 0) >= 100]
    learning = [c for c in courses if 0 < (c["progress"] or 0) < 100]
    avg = round(sum((c["progress"] or 0) for c in courses) / len(courses)) if courses else 0
    skills = []
    for c in completed:
        label = c["title"].replace(" Masterclass", "").replace(" Development", "").replace(" Database", "")
        if label not in skills:
            skills.append(label)
    connected = is_connected(session["user_id"], user_id, conn)
    conn_count = conn.execute("SELECT COUNT(*) FROM connections WHERE user_a=? OR user_b=?", (user_id, user_id)).fetchone()[0]
    conn.close()
    return render_template("learner_profile.html", learner=learner, courses=courses, completed=completed, learning=learning, avg_progress=avg, skills=skills, connected=connected, connection_count=conn_count)


@app.post("/api/connect/<int:user_id>")
def api_connect(user_id):
    if not user_logged_in():
        return {"ok": False, "error": "Login required"}, 401
    if user_id == session["user_id"]:
        return {"ok": False, "error": "You cannot connect with yourself."}, 400
    conn = get_db()
    if not conn.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        conn.close()
        return {"ok": False, "error": "Learner not found."}, 404
    a, b = connection_pair(session["user_id"], user_id)
    try:
        conn.execute("INSERT OR IGNORE INTO connections(user_a,user_b) VALUES(?,?)", (a, b))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "connected": True, "user_id": user_id}


@app.delete("/api/connect/<int:user_id>")
def api_disconnect(user_id):
    if not user_logged_in():
        return {"ok": False, "error": "Login required"}, 401
    a, b = connection_pair(session["user_id"], user_id)
    conn = get_db()
    conn.execute("DELETE FROM connections WHERE user_a=? AND user_b=?", (a, b))
    conn.commit(); conn.close()
    return {"ok": True, "connected": False, "user_id": user_id}


@app.route("/mycourse")
def mycourse():
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db(); courses = conn.execute("""SELECT c.*,e.progress,e.enrolled_at,e.completed_at,(SELECT percentage FROM test_attempts t WHERE t.user_id=e.user_id AND t.course_id=e.course_id ORDER BY t.percentage DESC,t.id DESC LIMIT 1) AS best_score,(SELECT tier FROM test_attempts t WHERE t.user_id=e.user_id AND t.course_id=e.course_id ORDER BY t.percentage DESC,t.id DESC LIMIT 1) AS best_tier FROM courses c JOIN enrollments e ON c.id=e.course_id WHERE e.user_id=? ORDER BY e.enrolled_at DESC""", (session["user_id"],)).fetchall(); conn.close()
    return render_template("mycourse.html", courses=courses)


@app.post("/enroll/<int:course_id>")
def enroll(course_id):
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db()
    if conn.execute("SELECT id FROM courses WHERE id=?", (course_id,)).fetchone():
        conn.execute("INSERT OR IGNORE INTO enrollments(user_id,course_id) VALUES(?,?)", (session["user_id"], course_id)); conn.commit()
    conn.close(); return redirect(url_for("course_detail", course_id=course_id))


@app.route("/course/<int:course_id>")
def course_detail(course_id):
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db(); course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone(); enrollment = conn.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (session["user_id"], course_id)).fetchone(); conn.close()
    if not course: return redirect(url_for("discover"))
    return render_template("course.html", course=course, enrollment=enrollment, youtube_id=youtube_id(course["video_url"]))


@app.post("/course/<int:course_id>/lesson")
def complete_lesson(course_id):
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db(); e = conn.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (session["user_id"], course_id)).fetchone()
    new_progress = int(e["progress"] or 0) if e else 0
    if e:
        course = conn.execute("SELECT lessons FROM courses WHERE id=?", (course_id,)).fetchone()
        lessons = max(1, int(course["lessons"] if course else 10))
        current = max(0, min(100, int(e["progress"] or 0)))
        completed_lessons = min(lessons, int(round((current * lessons) / 100)))
        next_lesson = min(lessons, completed_lessons + 1)
        new_progress = round((next_lesson / lessons) * 100)
        if next_lesson >= lessons:
            new_progress = 100
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_progress >= 100 else e["completed_at"]
        conn.execute("UPDATE enrollments SET progress=?,completed_at=? WHERE id=?", (new_progress, completed_at, e["id"]))
        conn.commit()
    conn.close()
    if request.headers.get("Accept", "").lower().find("application/json") >= 0 or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"ok": True, "progress": new_progress, "completed": new_progress >= 100, "course_id": course_id}
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/progress")
def progress():
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db(); rows = conn.execute("SELECT c.title,c.category,c.icon,c.accent,c.lessons,e.progress,e.enrolled_at FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=? ORDER BY e.enrolled_at DESC", (session["user_id"],)).fetchall(); conn.close()
    return render_template("progress.html", courses=rows)


@app.route("/test/<int:course_id>", methods=["GET", "POST"])
def course_test(course_id):
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    enrollment = conn.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (session["user_id"], course_id)).fetchone()
    conn.close()
    if not course: return redirect(url_for("discover"))
    if not enrollment:
        return redirect(url_for("course_detail", course_id=course_id))
    if int(enrollment["progress"] or 0) < 100:
        flash("Complete all course lessons before starting the final test.")
        return redirect(url_for("course_detail", course_id=course_id))
    questions = TESTS.get(course_id, TESTS[1])
    if request.method == "POST":
        answers = request.form
        score = sum(1 for i, q in enumerate(questions) if answers.get(f"q{i}") == str(q[2]))
        total = len(questions)
        percentage = round((score / total) * 100)
        tier, tier_key = certificate_tier(percentage)
        conn = get_db()
        cur = conn.execute("INSERT INTO test_attempts(user_id,course_id,score,total,percentage,tier,taken_at) VALUES(?,?,?,?,?,?,?)", (session["user_id"],course_id,score,total,percentage,tier,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        attempt_id = cur.lastrowid
        conn.commit()
        conn.close()
        return render_template("test_result.html", course=course, score=score, total=total, percentage=percentage, tier=tier, tier_key=tier_key, attempt_id=attempt_id, certificate_id=certificate_id(session["user_id"],course_id,attempt_id))
    conn = get_db()
    last = conn.execute("SELECT * FROM test_attempts WHERE user_id=? AND course_id=? ORDER BY id DESC LIMIT 1", (session["user_id"],course_id)).fetchone()
    conn.close()
    return render_template("course_test.html", course=course, questions=questions, last=last)


@app.route("/certificates")
def certificates():
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("""SELECT c.*, e.completed_at, ta.id AS attempt_id, ta.score, ta.total, ta.percentage, ta.tier, ta.taken_at
        FROM enrollments e JOIN courses c ON c.id=e.course_id
        JOIN test_attempts ta ON ta.id=(SELECT t2.id FROM test_attempts t2 WHERE t2.user_id=e.user_id AND t2.course_id=e.course_id ORDER BY t2.percentage DESC,t2.id DESC LIMIT 1)
        WHERE e.user_id=? AND e.progress>=100 AND ta.percentage>=50 ORDER BY ta.taken_at DESC""", (session["user_id"],)).fetchall()
    pending = conn.execute("""SELECT c.*,e.progress, (SELECT percentage FROM test_attempts t WHERE t.user_id=e.user_id AND t.course_id=e.course_id ORDER BY t.id DESC LIMIT 1) AS last_percentage
        FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=? AND e.progress>=100 AND NOT EXISTS (SELECT 1 FROM test_attempts t WHERE t.user_id=e.user_id AND t.course_id=e.course_id AND t.percentage>=50)""", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("certificates.html", certificates=rows, pending=pending)


@app.route("/certificate/<int:course_id>/download")
def certificate_download(course_id):
    if not user_logged_in(): return redirect(url_for("login"))
    conn=get_db()
    row=conn.execute("""SELECT c.title,c.category,ta.score,ta.total,ta.percentage,ta.tier,ta.id AS attempt_id,ta.taken_at,u.fullname
        FROM test_attempts ta JOIN courses c ON c.id=ta.course_id JOIN users u ON u.id=ta.user_id
        WHERE ta.user_id=? AND ta.course_id=? AND ta.percentage>=50 ORDER BY ta.percentage DESC,ta.id DESC LIMIT 1""", (session["user_id"],course_id)).fetchone()
    conn.close()
    if not row: return redirect(url_for("certificates"))
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase.pdfmetrics import stringWidth
    except ImportError: return "Please run: pip install -r requirements.txt",500
    W,H=landscape(A4); buf=BytesIO(); pdf=canvas.Canvas(buf,pagesize=(W,H))
    tier=row["tier"].upper(); palette={"DIAMOND":("#bfe9ff","#4bb6ff","#0a1726"),"GOLD":("#ffe7a0","#d8a52b","#211808"),"PLATINUM":("#eef3f8","#9eabb8","#111820")}; light,accent,dark=palette.get(tier,palette["GOLD"])
    def C(x): return colors.HexColor(x)
    pdf.setFillColor(C(dark)); pdf.rect(0,0,W,H,fill=1,stroke=0)
    # layered professional border
    pdf.setStrokeColor(C(accent)); pdf.setLineWidth(5); pdf.rect(28,28,W-56,H-56,fill=0,stroke=1)
    pdf.setStrokeColor(C(light)); pdf.setLineWidth(1.4); pdf.rect(39,39,W-78,H-78,fill=0,stroke=1)
    pdf.setStrokeColor(C(accent)); pdf.setLineWidth(.8); pdf.rect(52,52,W-104,H-104,fill=0,stroke=1)
    # corner ornaments
    for x,y in [(62,62),(W-62,62),(62,H-62),(W-62,H-62)]:
        pdf.setFillColor(C(accent)); pdf.circle(x,y,12,fill=0,stroke=1); pdf.circle(x,y,4,fill=1,stroke=0)
    pdf.setFillColor(C(light)); pdf.setFont("Helvetica-Bold",13); pdf.drawCentredString(W/2,H-88,"SKILLSHARE • LEARN. SHARE. GROW.")
    pdf.setFillColor(C(accent)); pdf.setFont("Helvetica-Bold",29); pdf.drawCentredString(W/2,H-128,"CERTIFICATE OF ACHIEVEMENT")
    pdf.setFillColor(C(light)); pdf.setFont("Helvetica",11); pdf.drawCentredString(W/2,H-153,"This certificate is proudly presented to")
    pdf.setFillColor(colors.white); pdf.setFont("Helvetica-Bold",31); pdf.drawCentredString(W/2,H-198,row["fullname"][:48])
    pdf.setFillColor(C(light)); pdf.setFont("Helvetica",10.5); pdf.drawCentredString(W/2,H-222,"for successfully completing the final assessment for")
    pdf.setFillColor(C(accent)); pdf.setFont("Helvetica-Bold",22); pdf.drawCentredString(W/2,H-253,row["title"][:55])
    # score badge
    bx,by= W/2, H-320; pdf.setFillColor(C(accent)); pdf.circle(bx,by,42,fill=0,stroke=1); pdf.setFillColor(C(light)); pdf.setFont("Helvetica-Bold",23); pdf.drawCentredString(bx,by-7,f"{row['percentage']}%")
    pdf.setFont("Helvetica-Bold",9); pdf.drawCentredString(bx,by-22,f"{row['score']}/{row['total']} SCORE")
    # tier ribbon
    rw,rh=170,38; rx=W/2-rw/2; ry=H-382; pdf.setFillColor(C(accent)); pdf.roundRect(rx,ry,rw,rh,12,fill=1,stroke=0); pdf.setFillColor(C(dark)); pdf.setFont("Helvetica-Bold",16); pdf.drawCentredString(W/2,ry+12,tier+" CERTIFICATE")
    pdf.setFillColor(C(light)); pdf.setFont("Helvetica",9); pdf.drawCentredString(W/2,ry-18,"Verified final assessment achievement")
    # footer fields
    pdf.setStrokeColor(C(accent)); pdf.line(90,112,250,112); pdf.line(W-250,112,W-90,112)
    pdf.setFillColor(C(light)); pdf.setFont("Helvetica",8.5); pdf.drawCentredString(170,98,"SKILLSHARE ACADEMIC SIGNATURE"); pdf.drawCentredString(W-170,98,"CERTIFICATION AUTHORITY")
    certno=certificate_id(session["user_id"],course_id,row["attempt_id"])
    pdf.setFillColor(colors.white); pdf.setFont("Helvetica-Bold",9); pdf.drawString(70,65,f"Certificate ID: {certno}"); pdf.drawRightString(W-70,65,f"Issued: {row['taken_at']}")
    pdf.save(); buf.seek(0)
    safe=re.sub(r"[^A-Za-z0-9_-]+","_",row["title"]).strip("_")
    return send_file(buf,as_attachment=True,download_name=f"SkillShare_{safe}_{tier}_Certificate.pdf",mimetype="application/pdf")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not user_logged_in(): return redirect(url_for("login"))
    conn = get_db(); user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            fullname=request.form.get("fullname","").strip(); email=request.form.get("email","").strip().lower(); phone=normalize_phone(request.form.get("phone",""))
            if not fullname or not valid_phone(phone): conn.close(); return render_template("settings.html",user=user,error="Enter a name and valid 10-digit mobile number.")
            other=conn.execute("SELECT id FROM users WHERE phone=? AND id<>?",(phone,user["id"])).fetchone(); email_other=conn.execute("SELECT id FROM users WHERE email=? AND id<>?",(email,user["id"])).fetchone()
            if other or email_other: conn.close(); return render_template("settings.html",user=user,error="Mobile number or email is already in use.")
            conn.execute("UPDATE users SET fullname=?,email=?,phone=? WHERE id=?",(fullname,email,phone,user["id"])); conn.commit(); session["fullname"],session["email"],session["phone"]=fullname,email,phone; user=conn.execute("SELECT * FROM users WHERE id=?",(user["id"],)).fetchone(); conn.close(); return render_template("settings.html",user=user,success="Profile details updated successfully.")
        if action == "password":
            current=request.form.get("current_password",""); new=request.form.get("new_password",""); confirm=request.form.get("confirm_password","")
            if not verify_password(user["password"],current): conn.close(); return render_template("settings.html",user=user,error="Current password is incorrect.")
            if len(new)<6 or new!=confirm: conn.close(); return render_template("settings.html",user=user,error="New passwords must match and contain at least 6 characters.")
            conn.execute("UPDATE users SET password=? WHERE id=?",(generate_password_hash(new),user["id"])); conn.commit(); conn.close(); return render_template("settings.html",user=user,success="Password changed successfully.")
    conn.close(); return render_template("settings.html",user=user)


# ---------------- ADMIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        conn=get_db(); admin=conn.execute("SELECT * FROM admins WHERE email=?",(email,)).fetchone()
        if admin and verify_password(admin["password"],password):
            if not is_password_hash(admin["password"]): upgrade_password(conn,"admins",admin["id"],password); conn.commit()
            session.clear(); session["is_admin"]=True; session["admin_id"]=admin["id"]; session["admin_name"]=admin["name"]; session["admin_email"]=admin["email"]; session["admin_phone"]=admin["phone"]
            conn.close(); return redirect(url_for("admin"))
        conn.close(); return render_template("admin_login.html",error="Invalid admin email or password.")
    return render_template("admin_login.html")


@app.route("/admin")
def admin():
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db()
    stats={"users":conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],"courses":conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0],"enrollments":conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0],"completed":conn.execute("SELECT COUNT(*) FROM enrollments WHERE progress>=100").fetchone()[0]}
    courses=conn.execute("SELECT c.*, (SELECT COUNT(*) FROM enrollments e WHERE e.course_id=c.id) AS enrolled_count FROM courses c ORDER BY c.id DESC").fetchall()
    users=conn.execute("SELECT u.id,u.fullname,u.email,u.phone,u.created_at,COUNT(e.id) AS enrolled_count,COALESCE(ROUND(AVG(e.progress)),0) AS avg_progress FROM users u LEFT JOIN enrollments e ON e.user_id=u.id GROUP BY u.id ORDER BY u.id DESC").fetchall()
    enrollments=conn.execute("SELECT e.id,e.enrolled_at,e.progress,e.completed_at,u.fullname,u.phone,c.title FROM enrollments e JOIN users u ON u.id=e.user_id JOIN courses c ON c.id=e.course_id ORDER BY e.enrolled_at DESC LIMIT 50").fetchall()
    admin_row=conn.execute("SELECT * FROM admins WHERE id=?",(session.get("admin_id"),)).fetchone(); conn.close()
    return render_template("admin.html",stats=stats,courses=courses,users=users,enrollments=enrollments,admin_row=admin_row)


@app.post("/admin/course/add")
def admin_add_course():
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    d=request.form
    try: rating=float(d.get("rating",4.8)); students=int(d.get("students",500)); lessons=max(1,int(d.get("lessons",10)))
    except ValueError: return redirect(url_for("admin"))
    conn=get_db(); conn.execute("INSERT INTO courses(title,description,icon,category,level,duration,rating,students,video_url,accent,lessons,featured) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(d.get("title","New Course").strip(),d.get("description","Learning program").strip(),d.get("icon","NEW").strip(),d.get("category","Technology"),d.get("level","Beginner"),d.get("duration","8h 30m"),rating,students,d.get("video_url","").strip(),d.get("accent","blue"),lessons,1 if d.get("featured") else 0)); conn.commit(); conn.close(); return redirect(url_for("admin"))


@app.route("/admin/course/<int:course_id>/edit",methods=["GET","POST"])
def admin_edit_course(course_id):
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db(); course=conn.execute("SELECT * FROM courses WHERE id=?",(course_id,)).fetchone()
    if not course: conn.close(); return redirect(url_for("admin"))
    if request.method=="POST":
        d=request.form
        try: rating=float(d.get("rating",4.8)); students=int(d.get("students",500)); lessons=max(1,int(d.get("lessons",10)))
        except ValueError: conn.close(); return redirect(url_for("admin_edit_course",course_id=course_id))
        conn.execute("UPDATE courses SET title=?,description=?,icon=?,category=?,level=?,duration=?,rating=?,students=?,video_url=?,accent=?,lessons=?,featured=? WHERE id=?",(d.get("title"),d.get("description"),d.get("icon",course["icon"]),d.get("category"),d.get("level"),d.get("duration"),rating,students,d.get("video_url",""),d.get("accent","blue"),lessons,1 if d.get("featured") else 0,course_id)); conn.commit(); conn.close(); return redirect(url_for("admin"))
    conn.close(); return render_template("admin_edit_course.html",course=course)


@app.post("/admin/course/<int:course_id>/delete")
def admin_delete_course(course_id):
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db(); conn.execute("DELETE FROM enrollments WHERE course_id=?",(course_id,)); conn.execute("DELETE FROM courses WHERE id=?",(course_id,)); conn.commit(); conn.close(); return redirect(url_for("admin"))


@app.post("/admin/user/<int:user_id>/delete")
def admin_delete_user(user_id):
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db(); conn.execute("DELETE FROM enrollments WHERE user_id=?",(user_id,)); conn.execute("DELETE FROM connections WHERE user_a=? OR user_b=?",(user_id,user_id)); conn.execute("DELETE FROM users WHERE id=?",(user_id,)); conn.commit(); conn.close(); return redirect(url_for("admin"))


@app.route("/admin/user/<int:user_id>/edit",methods=["GET","POST"])
def admin_edit_user(user_id):
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db(); user=conn.execute("SELECT id,fullname,email,phone FROM users WHERE id=?",(user_id,)).fetchone()
    if not user: conn.close(); return redirect(url_for("admin"))
    if request.method=="POST":
        d=request.form; fullname=d.get("fullname","").strip(); email=d.get("email","").strip().lower(); phone=normalize_phone(d.get("phone",""))
        if fullname and email and valid_phone(phone):
            other=conn.execute("SELECT id FROM users WHERE phone=? AND id<>?",(phone,user_id)).fetchone(); email_other=conn.execute("SELECT id FROM users WHERE email=? AND id<>?",(email,user_id)).fetchone()
            if not other and not email_other:
                conn.execute("UPDATE users SET fullname=?,email=?,phone=? WHERE id=?",(fullname,email,phone,user_id)); newpass=d.get("new_password","").strip()
                if newpass: conn.execute("UPDATE users SET password=? WHERE id=?",(generate_password_hash(newpass),user_id))
                conn.commit()
        conn.close(); return redirect(url_for("admin"))
    conn.close(); return render_template("admin_edit_user.html",user=user)


@app.route("/admin/settings",methods=["GET","POST"])
def admin_settings():
    if not admin_logged_in(): return redirect(url_for("admin_login"))
    conn=get_db(); admin_row=conn.execute("SELECT * FROM admins WHERE id=?",(session.get("admin_id"),)).fetchone()
    if request.method=="POST":
        action=request.form.get("action")
        if action=="profile":
            name=request.form.get("name","").strip(); phone=normalize_phone(request.form.get("phone",""))
            if not name or not valid_phone(phone): conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error="Enter a valid admin name and 10-digit mobile number.")
            conn.execute("UPDATE admins SET name=?,phone=?,phone_verified=0 WHERE id=?",(name,phone,admin_row["id"])); conn.commit(); session["admin_name"]=name; session["admin_phone"]=phone
            ok,msg=send_sms_otp(phone); admin_row=conn.execute("SELECT * FROM admins WHERE id=?",(admin_row["id"],)).fetchone(); conn.close()
            return render_template("admin_settings.html",admin_row=admin_row,otp_sent=ok,success=msg if ok else None,error=None if ok else msg,verify_phone=True)
        if action=="verify_phone":
            phone=admin_row["phone"]; ok,msg=verify_sms_otp(phone,request.form.get("otp",""))
            if ok:
                conn.execute("UPDATE admins SET phone_verified=1 WHERE id=?",(admin_row["id"],)); conn.commit(); admin_row=conn.execute("SELECT * FROM admins WHERE id=?",(admin_row["id"],)).fetchone(); conn.close(); return render_template("admin_settings.html",admin_row=admin_row,success="Admin mobile number verified. OTP password protection is active.")
            conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error=msg)
        if action=="send_password_otp":
            current=request.form.get("current_password",""); new=request.form.get("new_password",""); confirm=request.form.get("confirm_password","")
            if not verify_password(admin_row["password"],current): conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error="Current admin password is incorrect.")
            if len(new)<6 or new!=confirm: conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error="New passwords must match and contain at least 6 characters.")
            if not admin_row["phone_verified"]: conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error="Verify the admin mobile number first.")
            ok,msg=send_sms_otp(admin_row["phone"])
            if ok:
                session["pending_admin_password_hash"]=generate_password_hash(new); session["pending_admin_password_time"]=datetime.utcnow().isoformat()
            conn.close(); return render_template("admin_settings.html",admin_row=admin_row,otp_sent=ok,success=msg if ok else None,error=None if ok else msg,password_otp=True)
        if action=="verify_password_otp":
            pending_hash=session.get("pending_admin_password_hash")
            if not pending_hash: conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error="Request a password OTP first.")
            ok,msg=verify_sms_otp(admin_row["phone"],request.form.get("otp",""))
            if ok:
                conn.execute("UPDATE admins SET password=? WHERE id=?",(pending_hash,admin_row["id"])); conn.commit(); session.pop("pending_admin_password_hash",None); session.pop("pending_admin_password_time",None); conn.close(); return render_template("admin_settings.html",admin_row=admin_row,success="Admin password changed successfully after OTP verification.")
            conn.close(); return render_template("admin_settings.html",admin_row=admin_row,error=msg)
    conn.close(); return render_template("admin_settings.html",admin_row=admin_row)


@app.route("/admin/logout")
def admin_logout():
    session.clear(); return redirect(url_for("home"))


@app.route("/community")
def community():
    if not user_logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    people = conn.execute("""
        SELECT u.id, u.fullname,
               COUNT(DISTINCT e.course_id) AS course_count,
               COALESCE(ROUND(AVG(e.progress)),0) AS avg_progress,
               (SELECT COUNT(*) FROM connections x WHERE x.user_a=MIN(u.id, ?) AND x.user_b=MAX(u.id, ?)) AS connected
        FROM users u LEFT JOIN enrollments e ON e.user_id=u.id
        WHERE u.id<>? GROUP BY u.id ORDER BY connected DESC, u.fullname
    """, (session["user_id"], session["user_id"], session["user_id"])).fetchall()
    connection_count = conn.execute("SELECT COUNT(*) FROM connections WHERE user_a=? OR user_b=?", (session["user_id"], session["user_id"])).fetchone()[0]
    conn.close()
    return render_template("community.html", people=people, connection_count=connection_count)


@app.route("/connect")
def connect():
    return redirect(url_for("community"))
@app.route("/about")
def about(): return render_template("about.html")
@app.route("/contact")
def contact(): return render_template("contact.html")
@app.route("/privacy")
def privacy(): return render_template("privacy.html")
@app.route("/profile")
def profile():
    if not user_logged_in(): return redirect(url_for("login"))
    return redirect(url_for("settings"))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



