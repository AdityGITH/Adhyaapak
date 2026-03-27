from flask import Flask, render_template, request
import os
import cv2
import pytesseract
import requests
import time
from gtts import gTTS
from threading import Thread
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 👉 Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=2)
        data = response.json()
        return data[0]['meanings'][0]['definitions'][0]['definition']
    except:
        return "Meaning not found"


# 🔥 CLEAN TEXT FOR BETTER SPEECH
def clean_text_for_tts(text):
    text = text.replace("\n", " ")
    text = text.replace("- ", "")  # fix broken words
    text = " ".join(text.split())
    return text


# 🔊 BACKGROUND AUDIO GENERATION (CHUNKED)
def generate_audio(text):
    try:
        chunks = [text[i:i+200] for i in range(0, len(text), 200)]
        combined = None

        for i, chunk in enumerate(chunks):
            tts = gTTS(text=chunk, lang='en')
            temp_file = f"static/temp_{i}.mp3"
            tts.save(temp_file)

            audio = AudioSegment.from_mp3(temp_file)

            if combined is None:
                combined = audio
            else:
                combined += audio

        final_path = os.path.join("static", "speech.mp3")
        combined.export(final_path, format="mp3")

        # cleanup temp files
        for i in range(len(chunks)):
            os.remove(f"static/temp_{i}.mp3")

    except Exception as e:
        print("TTS Error:", e)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/upload', methods=['POST'])
def upload():
    start = time.time()

    image = request.files.get('image')

    if not image:
        return render_template("index.html", text="", meaning="", audio_ready=False)

    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)

    img = cv2.imread(image_path)

    if img is None:
        return render_template("index.html", text="", meaning="", audio_ready=False)

    # 🚀 FAST PREPROCESSING
    h, w = img.shape[:2]
    if w > 1000:
        scale = 1000 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # ⚡ OCR
    extracted_text = pytesseract.image_to_string(thresh)
    extracted_text = extracted_text.replace("\n", " ").strip()
    extracted_text = " ".join(extracted_text.split())

    # 📖 Meaning
    if extracted_text:
        first_word = extracted_text.split()[0].lower()
        meaning = get_meaning(first_word)
    else:
        meaning = ""

    # 🔊 Clean + Generate Audio (background)
    if extracted_text:
        cleaned_text = clean_text_for_tts(extracted_text)
        Thread(target=generate_audio, args=(cleaned_text,)).start()

    end = time.time()
    print(f"⚡ Processing Time: {round(end - start, 2)} sec")

    return render_template(
        "index.html",
        text=extracted_text,
        meaning=meaning,
        audio_ready=True if extracted_text else False
    )


if __name__ == "__main__":
    app.run(debug=True)