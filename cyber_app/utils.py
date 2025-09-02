# email_parser/utils.py
import re
from datetime import datetime

def extract_ack_no(subject):
    match = re.search(r"Acknowledgement No[.\- ]*\s*(\d+)", subject, re.IGNORECASE)
    return match.group(1) if match else None

def extract_month_from_string(mail_date_str):
    try:
        dt = datetime.strptime(mail_date_str.replace(" GMT", ""), "%A, %B %d, %Y %I:%M:%S %p")
        return dt.strftime("%B"), dt.month
    except Exception as e:
        print("\u274c MailDate parsing failed:", e)
        return None, None

def calculate_ageing_days1(date_str):
    try:
        dt = datetime.strptime(date_str.replace(":PM", "").replace(":AM", ""), "%d/%m/%Y %H:%M")
        return (datetime.now().date() - dt.date()).days
    except Exception as e:
        print("\u274c Date parsing failed:", e)
        return None
