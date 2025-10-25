import os
import imaplib
import email
from email.header import decode_header
import requests
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # Updated to current free model
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"  # Added ?key

def gemini_summarize(text):
    prompt = f"Summarize this email in 1-2 short sentences, including key content from the body and any urgency: {text[:1500]}"  # Explicit for content
    try:
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini summarize error: {e}")
        return "Summary failed—check email content manually"

def get_email_summary(max_emails=3):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK" or not messages[0]: return "No new emails"

        email_ids = messages[0].split()[-max_emails:]
        summaries = []

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK": continue
            msg = email.message_from_bytes(msg_data[0][1])

            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes): subject = subject.decode()
            sender = msg.get("From").split("<")[0].strip().strip('"')

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')

            # Ensure body is included in summary
            if not body.strip():
                summary = f"From {sender}: {subject} (No body content found)"
            else:
                summary = gemini_summarize(f"From: {sender}\nSubject: {subject}\nBody: {body}")

            summaries.append(summary)

        mail.close()
        mail.logout()
        return "\n\n".join(summaries) if summaries else "No summaries"

    except Exception as e:
        print(f"Email error: {e}")
        return "Email login failed"