import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError("EMAIL_ADDRESS or EMAIL_PASSWORD not set in environment")


def send_report_email(to_email, csv_path, pdf_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found")

    msg = EmailMessage()
    msg["Subject"] = "Your Social Sentiment Monitor Report"
    msg["From"] = EMAIL
    msg["To"] = to_email

    msg.set_content(
        "Hi,\n\n"
        "Here is the sentiment report you requested from Social Sentiment Monitor.\n\n"
        "Regards,\n"
        "Social Sentiment Monitor"
    )

    with open(csv_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="text",
            subtype="csv",
            filename="tweets.csv"
        )

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename="analysis.pdf"
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
