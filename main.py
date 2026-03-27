from flask import Flask, render_template, request
import os
import cv2
import pytesseract
import requests
import time

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 👉 Set path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=2)
        data = response.json()
        return data[0]['meanings'][0]['definitions'][0]['definition']
    except:
        return "Meaning not found"


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/upload', methods=['POST'])
def upload():
    start = time.time()

    image = request.files.get('image')

    if not image:
        return render_template("index.html", text="", meaning="No image")

    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)

    img = cv2.imread(image_path)

    if img is None:
        return render_template("index.html", text="", meaning="Invalid image")

    # 🚀 FAST PREPROCESSING
    h, w = img.shape[:2]

    if w > 1000:
        scale = 1000 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Optional threshold (improves clarity)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # 🚀 OCR (VERY FAST)
    extracted_text = pytesseract.image_to_string(thresh)

    extracted_text = extracted_text.replace("\n", " ").strip()
    extracted_text = " ".join(extracted_text.split())

    # Meaning
    if extracted_text:
        first_word = extracted_text.split()[0].lower()
        meaning = get_meaning(first_word)
    else:
        meaning = ""

    end = time.time()
    print(f"⚡ Time: {round(end - start, 2)} sec")

    return render_template("index.html", text=extracted_text, meaning=meaning)


if __name__ == "__main__":
    app.run(debug=True)