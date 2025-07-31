import os
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import smtplib
from email.message import EmailMessage
import time

# ---------- Skill Set ----------
REQUIRED_SKILLS = {
    "python", "java", "sql", "excel", "power bi", "machine learning", "deep learning",
    "html", "css", "javascript", "django", "communication", "data analysis"
}

# ---------- Helper Functions ----------
def extract_text_from_pdf(uploaded_file):
    try:
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.lower()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def match_skills(resume_text):
    matched = [skill for skill in REQUIRED_SKILLS if skill.lower() in resume_text]
    count = len(matched)
    if count >= 6:
        status = "Selected"
    elif 3 <= count < 6:
        status = "Waiting"
    else:
        status = "Rejected"
    return matched, status

def send_email(to_email, candidate_name, result, matched_skills):
    try:
        EMAIL_ADDRESS = st.secrets["EMAIL"]["ADDRESS"]
        EMAIL_PASSWORD = st.secrets["EMAIL"]["PASSWORD"]

        msg = EmailMessage()
        msg["Subject"] = "Resume Evaluation Result"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email

        body = f"""Hi {candidate_name},

Thank you for submitting your resume.

🧠 Skills matched: {', '.join(matched_skills) if matched_skills else 'None'}
📊 Evaluation Result: {result}

We appreciate your interest. We’ll be in touch if any suitable opportunity arises.

Regards,  
ResumeBot Team"""

        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        return True
    except Exception as e:
        st.error(f"❌ Email failed to send: {e}")
        return False

# ---------- Streamlit UI ----------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🧠")
st.title("📄 AI Resume Analyzer with Auto Mail ✉️")
st.write("Upload your resume PDF and get instant evaluation.")

# Form for input
with st.form("resume_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    resume = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])
    submitted = st.form_submit_button("Submit")

if submitted:
    if not name or not email or not resume:
        st.warning("Please fill all fields and upload a PDF.")
    else:
        with st.spinner("Analyzing your resume..."):
            resume_text = extract_text_from_pdf(resume)
            matched_skills, result = match_skills(resume_text)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # Save to CSV
            new_data = pd.DataFrame([{
                "Timestamp": timestamp,
                "Name": name,
                "Email": email,
                "Matched Skills": ", ".join(matched_skills),
                "Status": result
            }])
            if os.path.exists("scored_resumes.csv"):
                old_data = pd.read_csv("scored_resumes.csv")
                all_data = pd.concat([old_data, new_data], ignore_index=True)
            else:
                all_data = new_data
            all_data.to_csv("scored_resumes.csv", index=False)

            # Send email
            email_sent = send_email(email, name, result, matched_skills)

            if email_sent:
                st.success(f"✅ Result: {result}. An email has been sent to {email}.")
            else:
                st.error("⚠️ Failed to send email.")
