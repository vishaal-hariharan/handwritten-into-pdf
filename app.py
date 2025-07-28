import streamlit as st
import easyocr
from fpdf import FPDF
from PIL import Image
import os

reader = easyocr.Reader(['en'])

st.title("📝 Handwritten Text to PDF Converter")

uploaded_file = st.file_uploader("Upload Handwritten Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)

    if st.button("Convert to PDF"):
        with st.spinner("Extracting text..."):
            result = reader.readtext(uploaded_file, detail=0)
            extracted_text = "\n".join(result)

            st.subheader("Extracted Text:")
            st.text(extracted_text)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in extracted_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            output_path = "output.pdf"
            pdf.output(output_path)

            with open(output_path, "rb") as f:
                st.download_button("📄 Download PDF", f, file_name="converted.pdf")
