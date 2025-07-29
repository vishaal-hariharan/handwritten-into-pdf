import streamlit as st
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from fpdf import FPDF
import google.generativeai as genai

# Show Gemini SDK version (debug)
st.write("Gemini SDK version:", genai.__version__)

# Configure Gemini with API key from secrets
genai.configure(api_key=st.secrets["gemini_api_key"])

# Gemini text cleanup function (v1 format)
def gemini_clean_text(ocr_text):
    prompt = f"""
    The following text was extracted from a handwritten image using OCR. It may contain spelling and grammatical mistakes. Clean it up, fix spelling, punctuation, and formatting.

    OCR Text:
    {ocr_text}
    """
    model = genai.GenerativeModel(model_name="models/gemini-pro")
    response = model.generate_content([{"text": prompt}])
    return response.text.strip()

# EasyOCR setup
reader = easyocr.Reader(['en'])

# Streamlit UI setup
st.set_page_config(page_title="Smart OCR with Gemini", layout="centered")
st.title("🧠 ChatGPT-Style OCR with Gemini AI")
st.caption("Handwritten image → editable smart text → downloadable PDF")

# Upload section
uploaded_file = st.file_uploader("📤 Upload a Handwritten Image", type=['jpg', 'jpeg', 'png'])

# Preprocess image for better OCR
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

# Main logic
if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption="Original Image", use_column_width=True)

    if st.button("🔍 Extract & Clean Text"):
        with st.spinner("Processing..."):
            # Enhance image
            processed_image = preprocess_image(image)
            st.image(processed_image, caption="Processed Image", use_column_width=True)

            # Convert to NumPy for EasyOCR
            image_np = np.array(processed_image)

            try:
                result = reader.readtext(image_np, detail=0)
            except Exception as e:
                st.error(f"❌ OCR failed: {e}")
                st.stop()

            # Basic cleaning
            cleaned_lines = []
            for line in result:
                line = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                words = [word for word in line.split() if len(word) >= 2]
                if words:
                    cleaned_lines.append(" ".join(words))

            raw_text = "\n".join(cleaned_lines)

            # Try Gemini cleanup
            try:
                corrected_text = gemini_clean_text(raw_text)
            except Exception as e:
                corrected_text = raw_text
                st.warning(f"⚠️ Gemini cleanup failed. Showing raw text instead. ({e})")

            # Editable output
            st.subheader("✏️ Final Editable Text")
            final_text = st.text_area("Fix anything here before exporting:", value=corrected_text, height=300)

            # PDF export
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in final_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            output_path = "output.pdf"
            pdf.output(output_path)

            with open(output_path, "rb") as f:
                st.download_button("📄 Download Final PDF", f, file_name="handwritten_text_cleaned.pdf")
