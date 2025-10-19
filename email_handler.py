import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def get_email_summary(max_emails=5):
    """
    Fetch recent unread emails and return a summary
    Returns: String summary of unread emails
    """
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != "OK":
            return "No new emails"
        
        email_ids = messages[0].split()
        unread_count = len(email_ids)
        
        if unread_count == 0:
            return "No new emails 📭"
        
        # Get details of most recent emails
        recent_emails = []
        for email_id in email_ids[-max_emails:]:  # Get last N emails
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                from_ = msg.get("From")
                
                # Extract just the name or email
                if "<" in from_:
                    sender = from_.split("<")[0].strip().strip('"')
                else:
                    sender = from_.split("@")[0]
                
                recent_emails.append({
                    "from": sender,
                    "subject": subject[:50]  # Limit subject length
                })
                
            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        # Create summary
        if unread_count == 1:
            email_info = recent_emails[0]
            return f"1 email from {email_info['from']}"
        elif unread_count <= 3:
            senders = [e['from'] for e in recent_emails]
            return f"{unread_count} emails from {', '.join(senders)}"
        else:
            top_senders = [e['from'] for e in recent_emails[:2]]
            return f"{unread_count} emails ({', '.join(top_senders)} & more)"
            
    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP Error: {e}")
        return "Email login failed"
    except Exception as e:
        print(f"❌ Email error: {e}")
        return "Email check error"

def get_detailed_email_summary(max_emails=3):
    """
    Get more detailed email summary with subjects
    Returns: List of email dictionaries
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != "OK" or not messages[0]:
            return []
        
        email_ids = messages[0].split()
        emails = []
        
        for email_id in email_ids[-max_emails:]:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                from_ = msg.get("From")
                
                emails.append({
                    "from": from_,
                    "subject": subject,
                    "date": msg.get("Date")
                })
                
            except Exception as e:
                print(f"Error processing email: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        return emails
        
    except Exception as e:
        print(f"❌ Email fetch error: {e}")
        return []

# Test function
if __name__ == "__main__":
    print("Testing email summary...")
    summary = get_email_summary()
    print(f"Summary: {summary}")
    
    print("\nDetailed emails:")
    emails = get_detailed_email_summary()
    for i, email_data in enumerate(emails, 1):
        print(f"{i}. From: {email_data['from']}")
        print(f"   Subject: {email_data['subject']}")
        print()