from flask import Flask, render_template, request
import easyocr
import os
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

reader = easyocr.Reader(['en'])   # English OCR

# Loading FLAN-T5 model
model_name = "google/flan-t5-small"

tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

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

        if extracted_text.strip() == "":
            extracted_text = "No text detected"
            meaning = ""
        else:
            # Generate Meaning using FLAN-T5
            prompt = f"Explain the meaning of this text in simple English: {extracted_text}"

            inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)

            outputs = model.generate(
                **inputs,
                max_length=150,
                num_beams=2,
                early_stopping=True
            )

            meaning = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("Extracted Text:", extracted_text)
        print("Generated Meaning:", meaning)
        return render_template("index.html", text=extracted_text, meaning=meaning)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
