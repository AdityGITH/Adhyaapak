from flask import Flask, render_template, request, redirect, url_for, session
import easyocr
import os
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

app = Flask(__name__)
app.secret_key = "secret123"   # needed for login session

UPLOAD_FOLDER = "uploads"

reader = easyocr.Reader(['en'])

model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


# -------- LOGIN PAGE --------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # simple login check
        if username == "admin" and password == "1234":
            session['user'] = username
            return redirect(url_for('home'))

        return "Invalid Login"

    return render_template("login.html")


# -------- HOME PAGE --------
@app.route('/')
def home():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("index.html")


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# -------- IMAGE UPLOAD --------
@app.route('/upload', methods=['POST'])
def upload():

    if 'user' not in session:
        return redirect(url_for('login'))

    image = request.files['image']

    if image:
        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(image_path)

        result = reader.readtext(image_path)
        extracted_text = " ".join([res[1] for res in result])

        if extracted_text.strip() == "":
            extracted_text = "No text detected"
            meaning = ""

        else:
            prompt = f"Explain the meaning of this text in simple English: {extracted_text}"

            inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)

            outputs = model.generate(
                **inputs,
                max_length=150,
                num_beams=2,
                early_stopping=True
            )

            meaning = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return render_template("index.html", text=extracted_text, meaning=meaning)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)