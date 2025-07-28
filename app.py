import streamlit as st
import easyocr
from fpdf import FPDF
from PIL import Image
import numpy as np
import re
from textblob import TextBlob

# Initialize OCR
reader = easyocr.Reader(['en'])

st.title("📝 Handwritten Text to PDF Converter with Auto-Correction")

uploaded_file = st.file_uploader("Upload Handwritten Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption='Uploaded Image', use_column_width=True)

    if st.button("Convert to PDF"):
        with st.spinner("Extracting and correcting text..."):
            image_np = np.array(image)
            result = reader.readtext(image_np, detail=0)

            # Clean the text and filter out garbage
            cleaned_lines = []
            for line in result:
                line = re.sub(r'[^a-zA-Z0-9\s]', '', line)  # Remove special characters
                words = [word for word in line.split() if len(word) >= 3]
                if words:
                    cleaned_lines.append(" ".join(words))

            raw_text = "\n".join(cleaned_lines)

            # Auto-correct spelling using TextBlob
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

            pdf_output = "output.pdf"
            pdf.output(pdf_output)

            with open(pdf_output, "rb") as f:
                st.download_button("📄 Download PDF", f, file_name="corrected_text.pdf")

          
              
