from flask import Flask, render_template, request
import easyocr
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

reader = easyocr.Reader(['en'])   # English OCR

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/upload', methods=['POST'])
def upload():

    image = request.files['image']

    if image:
        image_path = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(image_path)

        # OCR Processing
        result = reader.readtext(image_path)

        extracted_text = " ".join([res[1] for res in result])

        # Safety check (important)
        if extracted_text.strip() == "":
            extracted_text = "No text detected"

        return render_template("index.html", text=extracted_text)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
