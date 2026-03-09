from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

from database import get_all_schedules
from email_utils import send_report_email

IST = pytz.timezone("Asia/Kolkata")

def daily_job():
    today = datetime.now(IST)
    weekday = today.strftime("%A")
    day = str(today.day)

    schedules = get_all_schedules()

    for email, freq, value in schedules:
        if freq == "daily":
            send_report_email(email, "output.csv", "report.pdf")

        elif freq == "weekly" and value == weekday:
            send_report_email(email, "output.csv", "report.pdf")

        elif freq == "monthly" and value == day:
            send_report_email(email, "output.csv", "report.pdf")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(daily_job, "cron", hour=9, minute=30)
    scheduler.start()
