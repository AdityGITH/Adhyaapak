from flask import Flask, render_template, request, redirect, url_for, session
import easyocr
import os
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- OCR MODEL ----------------
reader = easyocr.Reader(['en'])


# ---------------- DICTIONARY FUNCTION ----------------
def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url).json()

        meaning = response[0]['meanings'][0]['definitions'][0]['definition']
        return meaning

    except:
        return "Meaning not found"


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username,password) VALUES (?,?)",
                (username,password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for('login'))

        except:
            return "Username already exists"

    return render_template("register.html")


# ---------------- LOGIN PAGE ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('home'))

        return "Invalid Login"

    return render_template("login.html")


# ---------------- HOME PAGE ----------------
@app.route('/')
def home():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("index.html")


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.pop('user', None)
    return redirect(url_for('login'))


# ---------------- IMAGE UPLOAD + OCR ----------------
@app.route('/upload', methods=['POST'])
def upload():

    if 'user' not in session:
        return redirect(url_for('login'))

    image = request.files['image']

    if image:

        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(image_path)

        # OCR
        result = reader.readtext(image_path)

        extracted_text = " ".join([res[1] for res in result])

        if extracted_text.strip() == "":
            extracted_text = "No text detected"
            meaning = ""

        else:
            words = extracted_text.split()

            main_word = words[0].lower()
            meaning = get_meaning(main_word)

        return render_template(
            "index.html",
            text=extracted_text,
            meaning=meaning
        )

    return render_template("index.html")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
