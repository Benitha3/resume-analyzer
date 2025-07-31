import streamlit as st
import os
import fitz
import smtplib
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

# Secret config
EMAIL_ADDRESS = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]
GCREDS_JSON = json.loads(st.secrets["GCREDS_JSON"])

# Google Sheet Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(GCREDS_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open("Resume Submissions").worksheet("Submissions")

# Skill list
required_skills = {
    "python", "java", "sql", "excel", "power bi", "machine learning", "deep learning",
    "html", "css", "javascript", "django", "communication", "data analysis"
}

# Email messages
messages = {
    "Selected": "Dear {name},\n\nCongratulations! You are shortlisted.\n\nRegards,\nHR Team",
    "Waiting": "Dear {name},\n\nYour application is under review. We’ll contact you soon.\n\nRegards,\nHR Team",
    "Rejected": "Dear {name},\n\nUnfortunately, you are not shortlisted. Best wishes!\n\nRegards,\nHR Team"
}

def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text.lower()

def analyze_resume(text):
    matched = [skill for skill in required_skills if skill in text]
    count = len(matched)
    if count >= 6:
        return "Selected", matched
    elif 3 <= count < 6:
        return "Waiting", matched
    else:
        return "Rejected", matched

def send_email(to, name, status):
    msg = EmailMessage()
    msg["Subject"] = "Resume Status – " + status
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg.set_content(messages[status].format(name=name))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def save_to_google_sheet(name, email, status, skills):
    sheet.append_row([name, email, status, ', '.join(skills), str(datetime.now())])

# UI
st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.title("📄 AI Resume Analyzer + Email Bot 💌")

name = st.text_input("Candidate Name")
email = st.text_input("Candidate Email")
resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if st.button("Analyze Resume"):
    if not name or not email or not resume_file:
        st.warning("Please fill all fields and upload a resume.")
    else:
        resume_text = extract_text_from_pdf(resume_file)
        status, matched_skills = analyze_resume(resume_text)

        send_email(email, name, status)
        save_to_google_sheet(name, email, status, matched_skills)

        st.success(f"✅ {status}! Email sent to {email}")
        st.info(f"Matched Skills: {', '.join(matched_skills)}")
