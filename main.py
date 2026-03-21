from flask import Flask, render_template, request
import easyocr
import os
import cv2
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OCR
reader = easyocr.Reader(['en'], gpu=False)

# Dictionary
def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url).json()
        return response[0]['meanings'][0]['definitions'][0]['definition']
    except:
        return "Meaning not found"

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files['image']

    if image:
        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(image_path)

        # ✅ BETTER PREPROCESSING (fix mismatch issue)
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=1.2, fy=1.2)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        cv2.imwrite(image_path, thresh)

        # OCR
        result = reader.readtext(image_path, detail=0)

        # ✅ CLEAN TEXT (IMPORTANT FIX)
        extracted_text = " ".join(result)
        extracted_text = extracted_text.replace("\n", " ").strip()

        # remove double spaces
        extracted_text = " ".join(extracted_text.split())

        # meaning
        if extracted_text:
            first_word = extracted_text.split()[0].lower()
            meaning = get_meaning(first_word)
        else:
            meaning = ""

        return render_template(
            "index.html",
            text=extracted_text,
            meaning=meaning
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)