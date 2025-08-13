"""
AI Resume Optimiser & Generator 
-----------------------------------------------------
Reads resume → Optimises for ATS & readability → Saves ATS-friendly PDF
"""

import os
import cohere
import fitz
import docx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Times New Roman fonts
pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))

# ---------------------------
# CONFIGURATION
# ---------------------------
COHERE_API_KEY = "TnL82PgcDHnGbybPYa96TtpbqUFmuxWS54omZEOH"  
co = cohere.Client(COHERE_API_KEY)

# ---------------------------
# FILE READING FUNCTIONS
# ---------------------------

def extract_text_from_pdf(pdf_path):
    text = ""
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text += page.get_text()
    return text.strip()

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def get_resume_text(file_path):
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_text_from_docx(file_path)
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
    print(f"📄 High-readability ATS-friendly PDF saved as {filename}")

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
# MAIN EXECUTION
# ---------------------------

if __name__ == "__main__":
    print("\n📄 AI Resume Optimiser & Generator (Cohere)\n")

    resume_path = input("Enter path to your resume file (PDF/DOCX): ").strip()
    if not os.path.exists(resume_path):
        print("❌ File not found!")
        exit()

    print("\nExtracting text from resume...")
    resume_text = get_resume_text(resume_path)

    print("\nPaste the target job description below (end with a blank line):")
    job_lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        job_lines.append(line)
    job_description = "\n".join(job_lines)

    print("\nOptimising resume for ATS & readability... Please wait...")
    full_output = optimise_resume(resume_text, job_description)

    if "===OPTIMISED RESUME===" in full_output:
        parts = full_output.split("===OPTIMISED RESUME===")
        if len(parts) > 1:
            optimised_resume_text = parts[1].split("===EXPLANATION===")[0].strip()
            explanation_text = full_output.split("===EXPLANATION===")[1].strip() if "===EXPLANATION===" in full_output else ""
    else:
        optimised_resume_text = full_output
        explanation_text = ""

    # Saving clean resume
    with open("optimised_resume.txt", "w", encoding="utf-8") as f:
        f.write(optimised_resume_text)

    # Saving explanation separately
    if explanation_text:
        with open("ats_explanation.txt", "w", encoding="utf-8") as f:
            f.write(explanation_text)

    print("✅ Optimised resume saved as 'optimised_resume.txt'")
    if explanation_text:
        print("💡 ATS explanation saved as 'ats_explanation.txt'")

    save_as_pdf(optimised_resume_text)
