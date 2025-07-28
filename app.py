import streamlit as st
import easyocr
from fpdf import FPDF
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from textblob import TextBlob

reader = easyocr.Reader(['en'])

st.title("📝 Handwritten Text to PDF Converter (Improved Accuracy)")

uploaded_file = st.file_uploader("Upload Handwritten Image", type=['jpg', 'jpeg', 'png'])

def preprocess_image(image):
    # Convert to grayscale
    image = image.convert("L")

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Apply sharpening
    image = image.filter(ImageFilter.SHARPEN)

    # Resize (optional, but improves OCR accuracy)
    image = image.resize((image.width * 2, image.height * 2))

    return image.convert('RGB')  # EasyOCR expects RGB or numpy array

if uploaded_file is not None:
    original_image = Image.open(uploaded_file).convert('RGB')
    st.image(original_image, caption='Original Image', use_column_width=True)

    if st.button("Convert to PDF"):
        with st.spinner("Preprocessing image and extracting text..."):
            processed_image = preprocess_image(original_image)
            st.image(processed_image, caption="Processed Image", use_column_width=True)

            image_np = np.array(processed_image)
            result = reader.readtext(image_np, detail=0)

            # Clean and filter
            cleaned_lines = []
            for line in result:
                line = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                words = [word for word in line.split() if len(word) >= 3]
                if words:
                    cleaned_lines.append(" ".join(words))

            raw_text = "\n".join(cleaned_lines)

            # Spelling correction
            corrected_text = str(TextBlob(raw_text).correct())

            st.subheader("Corrected Text:")
            st.text(corrected_text)

            # Generate PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in corrected_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            output_path = "output.pdf"
            pdf.output(output_path)

            with open(output_path, "rb") as f:
                st.download_button("📄 Download PDF", f, file_name="corrected_text.pdf")
