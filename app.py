import streamlit as st
import easyocr
from fpdf import FPDF
from PIL import Image
import numpy as np
import io

reader = easyocr.Reader(['en'])

st.title("📝 Handwritten Text to PDF Converter")

uploaded_file = st.file_uploader("Upload Handwritten Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Load image with PIL
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption='Uploaded Image', use_column_width=True)

    if st.button("Convert to PDF"):
        with st.spinner("Extracting text..."):
            # Convert PIL image to NumPy array
            image_np = np.array(image)

            # Use EasyOCR on the array
            result = reader.readtext(image_np, detail=0)
            extracted_text = "\n".join(result)

            st.subheader("Extracted Text:")
            st.text(extracted_text)

            # Create a PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in extracted_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1)

            # Save and download
            pdf_output = "output.pdf"
            pdf.output(pdf_output)

            with open(pdf_output, "rb") as f:
                st.download_button("📄 Download PDF", f, file_name="converted.pdf")

         
