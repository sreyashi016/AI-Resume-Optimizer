import os
import cohere
import fitz
import docx
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------
# FONT REGISTRATION
# ---------------------------
try:
    pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
    pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))
except:
    pass  # fallback if fonts not found

# ---------------------------
# CONFIGURATION
# ---------------------------
COHERE_API_KEY = "TnL82PgcDHnGbybPYa96TtpbqUFmuxWS54omZEOH"
co = cohere.Client(COHERE_API_KEY)

# ---------------------------
# FILE READING FUNCTIONS
# ---------------------------
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text += page.get_text()
    return text.strip()

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def get_resume_text(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")

# ---------------------------
# PDF WRITING FUNCTION
# ---------------------------
def save_as_pdf(text, filename="optimised_resume.pdf"):
    """Saves clean ATS-friendly PDF with bold headings."""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    left_margin = 1 * inch
    right_margin = width - 1 * inch
    top_margin = height - 1 * inch
    bottom_margin = 1 * inch

    lines = text.split("\n")
    y_position = top_margin

    for line in lines:
        if line.strip() == "":
            y_position -= 14
            continue

        if line.strip().isupper() and len(line.strip()) <= 40:
            c.setFont("Times-Bold", 13)
            c.drawString(left_margin, y_position, line.strip())
            y_position -= 8
            c.setLineWidth(0.7)
            c.line(left_margin, y_position, right_margin, y_position)
            y_position -= 18
            continue
        else:
            c.setFont("Times-Roman", 11)

        # Wrap text
        words = line.split()
        current_line = ""
        for word in words:
            if c.stringWidth(current_line + word, "Times-Roman", 11) < (width - 2 * inch):
                current_line += word + " "
            else:
                c.drawString(left_margin, y_position, current_line.strip())
                y_position -= 14
                current_line = word + " "
        if current_line:
            c.drawString(left_margin, y_position, current_line.strip())
            y_position -= 14

        if y_position < bottom_margin:
            c.showPage()
            y_position = top_margin

    c.save()
    return filename

# ---------------------------
# COHERE OPTIMISATION
# ---------------------------
def optimise_resume(resume_text, job_description):
    prompt = f"""
You are an ATS optimisation expert and professional resume writer.
Your task:
1. Optimise the given resume so it scores very high on ATS systems for the provided job description.
2. Maintain very high readability for human reviewers.
3. Use strong action verbs, measurable achievements, and relevant industry keywords.
4. Keep formatting ATS-safe (plain text, no tables/images).
5. Section headings must be in ALL CAPS (e.g., "PROFESSIONAL EXPERIENCE").
6. Use bullet points where possible for experience and skills.
7. Do not use symbols like ** for bold — just plain text. 
8. Keep the structure: Contact Info → Summary → Skills → Experience → Education → Certifications (if any).

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return your answer in the following format:

===OPTIMISED RESUME===
<resume_here>

===EXPLANATION===
<explanation_here>
    """

    response = co.chat(
        model="command-r-plus",
        message=prompt,
        temperature=0.3
    )

    return response.text.strip()

# ---------------------------
# STREAMLIT APP
# ---------------------------
def main():
    st.title("📄 AI Resume Optimiser & Generator")
    st.write("Upload your resume and job description, and get an ATS-optimised version.")

    uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
    job_description = st.text_area("Paste Job Description", height=200)

    if uploaded_file and job_description:
        if st.button("Optimise Resume"):
            with st.spinner("Extracting resume and optimising..."):
                resume_text = get_resume_text(uploaded_file)
                full_output = optimise_resume(resume_text, job_description)

                if "===OPTIMISED RESUME===" in full_output:
                    optimised_resume_text = full_output.split("===OPTIMISED RESUME===")[1].split("===EXPLANATION===")[0].strip()
                    explanation_text = full_output.split("===EXPLANATION===")[1].strip() if "===EXPLANATION===" in full_output else ""
                else:
                    optimised_resume_text = full_output
                    explanation_text = ""

                st.subheader("✅ Optimised Resume")
                st.text_area("Optimised Resume", optimised_resume_text, height=400)

                if explanation_text:
                    st.subheader("💡 ATS Optimisation Explanation")
                    st.text_area("Explanation", explanation_text, height=300)

                # Save files
                txt_path = "optimised_resume.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(optimised_resume_text)

                pdf_path = save_as_pdf(optimised_resume_text)

                # Downloads
                st.download_button("⬇️ Download as TXT", data=open(txt_path, "rb"), file_name="optimised_resume.txt")
                st.download_button("⬇️ Download as PDF", data=open(pdf_path, "rb"), file_name="optimised_resume.pdf")

if __name__ == "__main__":
    main()
