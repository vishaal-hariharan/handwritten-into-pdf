import streamlit as st
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from fpdf import FPDF
import requests
import json

# Preprocess uploaded image
def preprocess_image(image):
    max_width = 1000
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((max_width, new_height))
    image = image.convert("L")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    return image.convert('RGB')

# Use Gemini API via REST (not SDK)
def gemini_clean_text(ocr_text):
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": st.secrets["gemini_api_key"]
    }
    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""The following text was extracted from a handwritten image using OCR. Clean it up, fix spelling, punctuation, and formatting:

{ocr_text}"""
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        raise Exception(f"Gemini API error: {response.status_code}, {response.text}")

# Streamlit UI
st.set_page_config(page_title="Smart OCR with Gemini", layout="centered")
st.title("🧠 ChatGPT-Style OCR (via Gemini REST API)")
st.caption("Upload a handwritten image → AI-corrected text → Editable → PDF")

uploaded_file = st.file_uploader("📤 Upload Handwritten Image", type=["jpg", "jpeg", "png"])
reader = easyocr.Reader(['en'])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Original Image", use_column_width=True)

    if st.button("🔍 Extract & Clean Text"):
        with st.spinner("Processing..."):
            processed_image = preprocess_image(image)
            image_np = np.array(processed_image)
            try:
                result = reader.readtext(image_np, detail=0)
            except Exception as e:
                st.error(f"❌ OCR failed: {e}")
                st.stop()

            cleaned_lines = []
            for line in result:
                line = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                words = [word for word in line.split() if len(word) >= 2]
                if words:
                    cleaned_lines.append(" ".join(words))
            raw_text = "\n".join(cleaned_lines)

            try:
                corrected_text = gemini_clean_text(raw_text)
            except Exception as e:
                corrected_text = raw_text
                st.warning(f"⚠️ Gemini cleanup failed. Showing raw text. ({e})")

            st.subheader("✏️ Editable Final Text")
            final_text = st.text_area("You can fix anything here:", value=corrected_text, height=300)

            # Generate PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in final_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            output_path = "output.pdf"
            pdf.output(output_path)

            with open(output_path, "rb") as f:
                st.download_button("📄 Download Final PDF", f, file_name="handwritten_text_cleaned.pdf")
