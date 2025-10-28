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

# FIXED: Use correct Gemini model name
GEMINI_MODEL = "gemini-1.5-flash-latest"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

def gemini_summarize(text):
    """Summarize email content using Gemini API"""
    # Keep prompt concise for better results
    prompt = f"Summarize in max 12 words: {text[:1000]}"
    
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 40  # Limit tokens for short summary
            }
        }
        
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "candidates" in data and data["candidates"]:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                summary = candidate["content"]["parts"][0]["text"].strip()
                # Remove quotes if present
                summary = summary.replace('"', '').replace("'", '')
                return summary
        
        print("⚠️ Gemini response missing expected structure")
        return "Summary unavailable"
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Gemini API error: {e}")
        return "API error"
    except Exception as e:
        print(f"❌ Gemini summarize error: {e}")
        return "Summary failed"


def get_email_summary(max_emails=3):
    """Fetch and summarize unread emails from Gmail"""
    
    # Validate credentials
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Email credentials missing in .env")
        return "Email config error"
    
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != "OK":
            print("❌ Email search failed")
            mail.close()
            mail.logout()
            return "Email search error"
        
        if not messages[0]:
            print("✅ No new emails found")
            mail.close()
            mail.logout()
            return "No new emails"

        # Get most recent emails
        email_ids = messages[0].split()[-max_emails:]
        summaries = []
        
        print(f"📧 Found {len(email_ids)} unread email(s)")

        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])

                # Decode subject
                subject_header = decode_header(msg["Subject"])[0]
                subject = subject_header[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(subject_header[1] or 'utf-8', errors='ignore')

                # Extract sender name
                from_header = msg.get("From", "Unknown")
                sender = from_header.split("<")[0].strip().strip('"')
                if not sender:
                    sender = from_header

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                            except:
                                continue
                else:
                    try:
                        body = msg.get_payload(decode=True).decode(errors='ignore')
                    except:
                        body = ""

                # Create summary text
                email_text = f"From: {sender}\nSubject: {subject}\n"
                if body.strip():
                    email_text += f"Body: {body[:500]}"  # Limit body length
                else:
                    email_text += "Body: (empty)"

                # Generate AI summary
                summary = gemini_summarize(email_text)
                
                # Fallback to manual summary if AI fails
                if summary in ["Summary failed", "API error", "Summary unavailable"]:
                    summary = f"{sender}: {subject[:30]}"
                
                summaries.append(summary)
                print(f"  ✅ Summarized: {summary}")

            except Exception as e:
                print(f"  ⚠️ Error processing email {email_id}: {e}")
                continue

        mail.close()
        mail.logout()
        
        # Combine summaries
        if summaries:
            # Join with separator for scrolling
            full_summary = " | ".join(summaries)
            
            # Ensure it's not too long (LCD will scroll it)
            if len(full_summary) > 300:
                full_summary = full_summary[:297] + "..."
            
            print(f"📨 Final summary: {full_summary}")
            return full_summary
        else:
            return "Email processing failed"

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP error: {e}")
        return "Email login failed"
    except Exception as e:
        print(f"❌ Email error: {e}")
        return "Email check error"


# Test function
if __name__ == "__main__":
    print("Testing email handler...")
    result = get_email_summary()
    print(f"\nResult: {result}")