import streamlit as st
import easyocr
from fpdf import FPDF
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
from textblob import TextBlob

# Initialize OCR reader
reader = easyocr.Reader(['en'])

st.title("📝 Handwritten Text to PDF Converter (Auto-corrected & Improved)")

uploaded_file = st.file_uploader("Upload Handwritten Image", type=['jpg', 'jpeg', 'png'])

# 🧠 Image preprocessing function
def preprocess_image(image):
    # Resize if too large (limit to 1000px width to prevent Streamlit crash)
    max_width = 1000
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((max_width, new_height))

    # Convert to grayscale
    image = image.convert("L")

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Apply sharpening
    image = image.filter(ImageFilter.SHARPEN)

    return image.convert('RGB')

# 🖼️ If user uploads an image
if uploaded_file is not None:
    try:
        original_image = Image.open(uploaded_file).convert('RGB')
        st.image(original_image, caption='Original Image', use_column_width=True)

        if st.button("Convert to PDF"):
            with st.spinner("Preprocessing image and extracting text..."):
                processed_image = preprocess_image(original_image)
                st.image(processed_image, caption="Processed Image", use_column_width=True)

                # Convert to NumPy array
                image_np = np.array(processed_image)

                # Run OCR safely
                try:
                    result = reader.readtext(image_np, detail=0)
                except Exception as e:
                    st.error(f"❌ OCR failed: {e}")
                    st.stop()

                # Clean and filter lines
                cleaned_lines = []
                for line in result:
                    line = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                    words = [word for word in line.split() if len(word) >= 3]
                    if words:
                        cleaned_lines.append(" ".join(words))

                raw_text = "\n".join(cleaned_lines)

                # Run spelling correction safely
                try:
                    corrected_text = str(TextBlob(raw_text).correct())
                except Exception as e:
                    st.warning("⚠️ Spell correction failed. Showing raw OCR text.")
                    corrected_text = raw_text

                st.subheader("Corrected Text:")
                st.text(corrected_text)

                # Create PDF
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

    except Exception as err:
        st.error(f"🚫 Something went wrong: {err}")
