# alert.py
import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_TO = os.getenv("ALERT_TO", SMTP_USER)

def send_alert_email(channel: str, detections):
    subject = f"[ALERT] Threat on {channel}"
    body = f"Detections on {channel}:\n\n{detections}\n\nAutomated alert."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_TO

    if not SMTP_USER or not SMTP_PASS:
        print("SMTP not configured — would send email:", subject)
        return

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [addr.strip() for addr in ALERT_TO.split(",")], msg.as_string())
        print("Email sent for", channel)
    except Exception as e:
        print("Email send failed:", e)
