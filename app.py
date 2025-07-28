import streamlit as st
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from textblob import TextBlob
from fpdf import FPDF

# Initialize the OCR reader
reader = easyocr.Reader(['en'])

st.set_page_config(page_title="ChatGPT-Style OCR", layout="centered")

st.title("🧠 ChatGPT-Style OCR for Handwritten Text")
st.caption("Smart preprocessing, auto-correction, editable output & PDF download")

uploaded_file = st.file_uploader("📤 Upload a Handwritten Image", type=['jpg', 'jpeg', 'png'])

def preprocess_image(image):
    max_width = 1000
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((max_width, new_height))

    # Grayscale + Contrast + Sharpening
    image = image.convert("L")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)

    return image.convert('RGB')

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption="Original Handwritten Image", use_column_width=True)

    if st.button("🔍 Extract Text"):
        with st.spinner("Processing image and running OCR..."):
            processed_image = preprocess_image(image)
            st.image(processed_image, caption="Preprocessed Image", use_column_width=True)

            image_np = np.array(processed_image)
            try:
                result = reader.readtext(image_np, detail=0)
            except Exception as e:
                st.error(f"❌ OCR failed: {e}")
                st.stop()

            # Clean and join lines
            raw_lines = []
            for line in result:
                line = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                words = [w for w in line.split() if len(w) >= 2]
                if words:
                    raw_lines.append(" ".join(words))

            raw_text = "\n".join(raw_lines)

            # Optional spell correction
            st.markdown("### 🛠️ Auto Correction")
            apply_correction = st.checkbox("Apply Spelling Correction (TextBlob)", value=True)

            if apply_correction:
                try:
                    corrected_text = str(TextBlob(raw_text).correct())
                except Exception:
                    corrected_text = raw_text
                    st.warning("Correction failed — using raw OCR text.")
            else:
                corrected_text = raw_text

            # Editable Text Box
            st.markdown("### ✍️ Final Editable Text")
            final_text = st.text_area("Edit the extracted text before download:", value=corrected_text, height=300)

            # Download as PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in final_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            pdf_output = "final_output.pdf"
            pdf.output(pdf_output)

            with open(pdf_output, "rb") as f:
                st.download_button("📄 Download as PDF", f, file_name="handwritten_text.pdf")



  
