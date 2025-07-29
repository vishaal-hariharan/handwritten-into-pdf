import streamlit as st
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from fpdf import FPDF
import google.generativeai as genai

# Configure Gemini using secret key
genai.configure(api_key=st.secrets["gemini_api_key"])

# Gemini-powered cleanup function
def gemini_clean_text(ocr_text):
    prompt = f"""
    The following text was extracted from a handwritten image using OCR. It may contain spelling and grammatical mistakes. Clean it up, fix spelling, punctuation, and formatting.

    OCR Text:
    {ocr_text}
    """
    # ✅ Use the full model path here with default v1 API
    model = genai.GenerativeModel(model_name="models/gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()


# OCR setup
reader = easyocr.Reader(['en'])

# App UI
st.set_page_config(page_title="Smart OCR with Gemini", layout="centered")
st.title("🧠 ChatGPT-Style OCR with Gemini AI")
st.caption("Handwritten image → editable smart text → PDF")

uploaded_file = st.file_uploader("📤 Upload a Handwritten Image", type=['jpg', 'jpeg', 'png'])

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

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption="Original Image", use_column_width=True)

    if st.button("🔍 Extract & Clean Text"):
        with st.spinner("Processing..."):
            processed_image = preprocess_image(image)
            st.image(processed_image, caption="Processed Image", use_column_width=True)

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

            st.subheader("✏️ Final Editable Text")
            final_text = st.text_area("You can manually fix if needed before PDF export:", value=corrected_text, height=300)

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
