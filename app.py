from flask import Flask, render_template, request, redirect, url_for
import os
import fitz
import pytesseract
from PIL import Image
import sqlite3
import json
import re
import pandas as pd
from datetime import datetime, timedelta
from google import genai  
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from flask import flash



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'iiiititite-change-this-in-production') 
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = genai.Client(api_key="AIzaSyDMUK_M2NTADXus2wiFSkYM4yv_cLH_kiY")

DB = "bills.db"


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bill_filename TEXT,
            item TEXT,
            category TEXT,
            amount REAL,
            date TEXT,
            remark TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            amount REAL,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            created_at TEXT
        )
        """)
        
        # Migrate existing data: add user_id column if it doesn't exist
        try:
            conn.execute("ALTER TABLE bill_items ADD COLUMN user_id INTEGER")
            # Set default user_id to 1 for existing records (or handle as needed)
            conn.execute("UPDATE bill_items SET user_id = 1 WHERE user_id IS NULL")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute("ALTER TABLE reminders ADD COLUMN user_id INTEGER")
            conn.execute("UPDATE reminders SET user_id = 1 WHERE user_id IS NULL")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
init_db()


def require_login(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_user_id():
    """Get current user ID from session"""
    return session.get('user_id')


def extract_text(file_path):
    text = ""
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        for page in doc:
            page_text = page.get_text().strip()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            for page_num in range(len(doc)):
                pix = doc[page_num].get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img) + "\n"
    else:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
    return text.strip()

def ask_llm(text):
    prompt = f"""
You are a bill categorizer. Extract items and assign categories.
Categories: Electricity, Grocery, Internet, Medical, Restaurant, Clothing, Entertainment.
If no match, use a suitable new category.
Follow the below instructions properly
important points to remember : categorize the bill in a genralised format like if any medical store bill
then send it in health category if bill of restorant then that should go in food and so on...
and also dont exclude components from bill only send category wise data dont exclude tax ,gst counter charge etc.
Return JSON in format:
[
  {{"item": "Milk", "category": "Grocery", "amount": "50"}},
  {{"item": "Jeans", "category": "Clothing", "amount": "1200"}}
]
Bill Text:
{text}
"""
    try:
        response = client.models.generate_content(
          model="gemini-2.0-flash",
           contents=prompt
        )
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception:
        return []


def get_existing_categories():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("SELECT DISTINCT category FROM bill_items").fetchall()
    return [r[0].lower() for r in rows]


@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for("dashboard"))
    return render_template("frist.html")


@app.route("/upload", methods=["POST"])
@require_login
def upload():
    user_id = get_user_id()
    file = request.files.get("bill")
    today_str = datetime.now().strftime("%Y-%m-%d")

    with sqlite3.connect(DB) as conn:
        existing_categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM bill_items WHERE user_id=?", (user_id,)).fetchall()]

        
        if file and file.filename != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            if file.filename.lower().endswith(".csv"):
                df = pd.read_csv(filepath)
                for _, row in df.iterrows():
                    category = str(row.get("category") or "Uncategorized").strip().title()
                    matched_category = next((c for c in existing_categories if c.lower() == category.lower()), category)
                    conn.execute(
                        "INSERT INTO bill_items (user_id, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            user_id,
                            row.get("item"),
                            matched_category,
                            float(row.get("amount", 0) or 0),
                            str(row.get("date") or today_str),
                            row.get("remark", "Uploaded CSV")
                        )
                    )
            else:
                text = extract_text(filepath)
                items = ask_llm(text)

                if items:
                    for item in items:
                        category = str(item.get("category") or "Uncategorized").strip().title()
                        matched_category = next((c for c in existing_categories if c.lower() == category.lower()), category)
                        conn.execute(
                            "INSERT INTO bill_items (user_id, bill_filename, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                user_id,
                                file.filename,
                                item.get("item"),
                                matched_category,
                                float(item.get("amount", 0) or 0),
                                today_str,
                                "Uploaded Bill"
                            )
                        )
                else:
                    
                    conn.execute(
                        "INSERT INTO bill_items (user_id, bill_filename, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, file.filename, file.filename, "Uncategorized", 0.0, today_str, "Uploaded file")
                    )

        payment_to = request.form.get("payment_to")
        amount = request.form.get("amount")
        date = request.form.get("date")
        remark = request.form.get("remark", "")
        category = str(request.form.get("category") or "Manual Entry").strip().title()

        if payment_to and amount and date:
            matched_category = next((c for c in existing_categories if c.lower() == category.lower()), category)
            conn.execute(
                "INSERT INTO bill_items (user_id, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, payment_to, matched_category, float(amount), date, remark)
            )

        conn.commit()

    return redirect(url_for("dashboard"))


@app.route('/categories')
@require_login
def categories():
    user_id = get_user_id()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT category, SUM(amount) FROM bill_items WHERE user_id=? GROUP BY category", (user_id,))
    categories = c.fetchall()
    conn.close()
    return render_template('category.html', categories=categories)

@app.route("/category_details/<category>")
@require_login
def category_details(category):
    return details(category)

@app.route("/add_bill_page")
@require_login
def add_bill_page():
    return render_template("index.html")

@app.route("/manual_add", methods=["POST"])
@require_login
def manual_add():
    user_id = get_user_id()
    payment_to = request.form.get("payment_to")
    amount = request.form.get("amount")
    date = request.form.get("date")
    remark = request.form.get("remark", "")
    category = str(request.form.get("category") or "Manual Entry").strip().title()

    if payment_to and amount and date:
        with sqlite3.connect(DB) as conn:
            existing_categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM bill_items WHERE user_id=?", (user_id,)).fetchall()]
            matched_category = next((c for c in existing_categories if c.lower() == category.lower()), category)
            
            conn.execute(
                "INSERT INTO bill_items (user_id, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, payment_to, matched_category, float(amount), date, remark)
            )
            conn.commit()

    return redirect(url_for("dashboard"))

@app.route("/add_category_page")
@require_login
def add_category_page():
    return render_template("add_category.html")

@app.route("/save_category", methods=["POST"])
@require_login
def save_category():
    user_id = get_user_id()
    category = request.form.get("category", "").strip()
    if category:
        with sqlite3.connect(DB) as conn:
            conn.execute(
                "INSERT INTO bill_items (user_id, item, category, amount, date, remark) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, "Category Placeholder", category, 0.0, datetime.now().strftime("%Y-%m-%d"), "Category created")
            )
            conn.commit()
    return redirect(url_for("categories"))

@app.route("/dashboard")
@require_login
def dashboard():
    user_id = get_user_id()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    c.execute("SELECT SUM(amount) FROM bill_items WHERE user_id=?", (user_id,))
    total_expense = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM bill_items WHERE user_id=? AND date=?", (user_id, str(today)))
    today_expense = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM bill_items WHERE user_id=? AND date BETWEEN ? AND ?", (user_id, str(week_ago), str(today)))
    week_expense = c.fetchone()[0] or 0

    last7_days, last7_values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c.execute("SELECT SUM(amount) FROM bill_items WHERE user_id=? AND date=?", (user_id, str(d)))
        val = c.fetchone()[0] or 0
        last7_days.append(d.strftime("%d %b"))
        last7_values.append(val)

    c.execute("SELECT category, SUM(amount) FROM bill_items WHERE user_id=? GROUP BY category", (user_id,))
    rows = c.fetchall()
    category_labels = [r[0] for r in rows]
    category_values = [r[1] for r in rows]

    c.execute("SELECT * FROM bill_items WHERE user_id=? ORDER BY date DESC, id DESC LIMIT 7", (user_id,))
    records = c.fetchall()
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)  
    c.execute( "SELECT * FROM reminders WHERE user_id=? AND (due_date=? OR due_date=?) ORDER BY due_date ASC",
        (user_id, str(today), str(tomorrow)))
    upcoming_reminders = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_expense=total_expense,
        today_expense=today_expense,
        week_expense=week_expense,
        last7_days=last7_days,
        last7_values=last7_values,
        category_labels=category_labels,
        category_values=category_values,
        records=records,
        upcoming_reminders=upcoming_reminders
    )

@app.route("/details/<category>")
@require_login
def details(category):
    user_id = get_user_id()
    with sqlite3.connect(DB) as conn:
        records = conn.execute("SELECT * FROM bill_items WHERE user_id=? AND category=?", (user_id, category)).fetchall()
    return render_template("details.html", records=records, category=category)

@app.route("/delete/<int:id>")
@require_login
def delete_record(id):
    user_id = get_user_id()
    next_page = request.args.get('next') or url_for("dashboard")  # fallback to dashboard
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM bill_items WHERE id=? AND user_id=?", (id, user_id))
        conn.commit()
    return redirect(next_page)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@require_login
def edit_record(id):
    user_id = get_user_id()
    with sqlite3.connect(DB) as conn:
        if request.method == "POST":
            item = request.form.get("item")
            category = request.form.get("category")
            amount = request.form.get("amount")
            remark = request.form.get("remark")
            conn.execute("UPDATE bill_items SET item=?, category=?, amount=?, remark=? WHERE id=? AND user_id=?",
                         (item, category, float(amount), remark, id, user_id))
            conn.commit()
            return redirect(url_for("dashboard"))
        record = conn.execute("SELECT * FROM bill_items WHERE id=? AND user_id=?", (id, user_id)).fetchone()
        if not record:
            return redirect(url_for("dashboard"))
    return render_template("edit.html", record=record)


@app.route("/talky")
@require_login
def talky():
    return render_template("talky.html")

@app.route("/talky_query", methods=["POST"])
@require_login
def talky_query():
    user_id = get_user_id()
    user_msg = request.json.get("message", "")

    
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("SELECT * FROM bill_items WHERE user_id=?", (user_id,)).fetchall()
        

    
    prompt = f"""
You are an expense assistant. A user asks: "{user_msg}"
The user has the following expense data: {rows}
Provide a short answer based on the data.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        ai_text = response.text.strip()
    except Exception:
        ai_text = "Sorry, I cannot process your request right now."

    return {"response": ai_text}


@app.route("/add_reminder")
@require_login
def add_reminder():
    return render_template("add_reminder.html")

@app.route("/save_reminder", methods=["POST"])
@require_login
def save_reminder():
    user_id = get_user_id()
    title = request.form.get("title")
    amount = request.form.get("amount")
    due_date = request.form.get("due_date")
    description = request.form.get("description", "")

    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO reminders (user_id, title, description, amount, due_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, description, float(amount), due_date)
        )
        conn.commit()
    return redirect(url_for("dashboard"))



@app.route("/delete_reminder/<int:id>")
@require_login
def delete_reminder(id):
    user_id = get_user_id()
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (id, user_id))
        conn.commit()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/report")
@require_login
def report():
    """Display all transactions for the logged-in user with remarks and amounts"""
    user_id = get_user_id()
    with sqlite3.connect(DB) as conn:
        records = conn.execute(
            "SELECT id, item, category, amount, date, remark FROM bill_items WHERE user_id=? ORDER BY date DESC, id DESC",
            (user_id,)
        ).fetchall()
    
    total_amount = sum(r[3] for r in records) if records else 0
    
    return render_template("report.html", records=records, total_amount=total_amount)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        age = request.form.get("age")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect(DB) as conn:
                conn.execute(
                    "INSERT INTO users (name, username, password, age, created_at) VALUES (?, ?, ?, ?, ?)",
                    (name, username, hashed_password, age, created_at)
                )
                conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists! Please choose another."
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("email", "")

        password = request.form.get("password", "")

        
        if not username.strip() or not password.strip():
            return render_template("login.html", error="Please enter both username and password.")

        username = username.strip()
        password = password.strip()

        with sqlite3.connect(DB) as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (username,)
            ).fetchone()

     
        if user is None:
            return render_template("login.html", error="No such user found. Please sign up first.")

        stored_hash = user[3] 

        
        if check_password_hash(stored_hash, password):
            session["user_id"] = user[0]
            session["username"] = user[2]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid password. Please try again.")

    return render_template("login.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))




if __name__ == "__main__":
    # For production, use: gunicorn app:app
    # For development:
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
