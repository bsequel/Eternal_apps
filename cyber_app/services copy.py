from __future__ import print_function
import os, re, json, base64
from pathlib import Path
from datetime import datetime

import pdfplumber
from pypdf import PdfReader, PdfWriter

# Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from .models import CyberCellReport

User = get_user_model()

# ─────────────── Config ─────────────── #
# SCOPES = ["https://www.googleapis.com/auth/gmail.modify","https://www.googleapis.com/auth/gmail.readonly"]
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
PDF_PASSWORD = "Zomato@123"
SUBJECT_KEYWORD = "NCRP MHA Acknowledgement No"

TOKEN_FILE = settings.GOOGLE_TOKEN_PATH
CREDENTIALS_FILE = settings.GOOGLE_CREDENTIALS_PATH
SOURCE_DIR = settings.EMAIL_PDF_SOURCE
DECRYPTED_DIR = settings.EMAIL_PDF_DECRYPTED


# ─────────────── Gmail Auth ─────────────── #
def save_tokens(creds: Credentials):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


# def load_tokens():
#     if not os.path.exists(TOKEN_FILE):
#         raise "ppp"
#     return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
def load_tokens():
    """Load tokens from token.json file"""
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    return Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = load_tokens()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_tokens(creds)
        # else:
        #     flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        #     creds = flow.run_local_server(port=0)
        #     save_tokens(creds)
    return creds


# ─────────────── Utils ─────────────── #
def extract_ack_no(subject):
    match = re.search(r"Acknowledgement No[.\- ]*\s*(\d+)", subject, re.IGNORECASE)
    return match.group(1) if match else None


def remove_pdf_password(input_path, output_path, password):
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            if reader.decrypt(password) == 0:
                print(f"❌ Incorrect password for {input_path}")
                return False
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        print(f"🔓 Decrypted: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to decrypt {input_path}: {e}")
        return False


def get_message_attachments(service, message_id):
    attachments = []
    try:
        msg = service.users().messages().get(userId="me", id=message_id).execute()
        parts = msg["payload"].get("parts", [msg["payload"]])
        for part in parts:
            if part.get("filename"):
                attachment_id = part["body"].get("attachmentId")
                if attachment_id:
                    attachment = service.users().messages().attachments().get(
                        userId="me", messageId=message_id, id=attachment_id
                    ).execute()
                    data = attachment["data"]
                    file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))
                    attachments.append({"filename": part["filename"], "data": file_data})
    except Exception as e:
        print(f"❌ Error getting attachments: {e}")
    return attachments


# ─────────────── Fetch PDFs ─────────────── #
def fetch_and_decrypt_pdfs():
    decrypted_paths = []
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        query = f'is:unread subject:"{SUBJECT_KEYWORD}"'
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])

        print(f"📧 Found {len(messages)} unread emails")

        for msg in messages:
            message = service.users().messages().get(userId="me", id=msg["id"]).execute()
            headers = message["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")

            if SUBJECT_KEYWORD.lower() not in subject.lower():
                continue

            ack_no = extract_ack_no(subject)
            if not ack_no:
                continue

            attachments = get_message_attachments(service, msg["id"])
            for att in attachments:
                ext = os.path.splitext(att["filename"])[1] or ".pdf"
                raw_path = SOURCE_DIR / f"{ack_no}{ext}"
                dec_path = DECRYPTED_DIR / f"{ack_no}{ext}"

                with open(raw_path, "wb") as f:
                    f.write(att["data"])
                print(f"📥 Downloaded: {raw_path}")

                if remove_pdf_password(raw_path, dec_path, PDF_PASSWORD):
                    decrypted_paths.append(dec_path)

            # mark read
            try:
                service.users().messages().modify(
                    userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            except Exception as e:
                print(f"⚠️ Could not mark as read: {e}")

    except Exception as e:
        print(f"❌ Gmail API Error: {e}")

    return decrypted_paths


# ─────────────── Data Extraction ─────────────── #
def extract_structured_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    cyber_data, line_items, count = {}, {}, 0
    for line in lines:
        # print(line)
        words = line.split()
        if "Sent:" in line:
            cyber_data["MailDate"] = line.replace("Sent:", "").strip()
        elif "Mobile" in line and words:
            cyber_data.setdefault("Mobile", []).append(words[-1])
        elif "Email" in line and "@" in line:
            cyber_data["Email"] = words[-1]
        elif "Address" in line:
            cyber_data["Address"] = line.split("Address")[-1].strip()
        elif "State /District /Police Station" in line:
            cyber_data["Police_Station_Address"] = line.split("Police Station")[-1].strip()
        elif "Acknowledgement No." in line:
            cyber_data["RefNo"] = words[-1]
        elif "Name" in line:
            # print(line,"========")
            pattern = re.compile(r'[^a-zA-Z0-9\s]')
            if pattern.search(line):
                pass
            else:
                cyber_data["Name"] = line.split("Name")[-1].strip()
        elif "Total Fraudulent Amount" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                cyber_data["Total_Fraudulent_Amount"] = parts[1].strip()
        elif "Account Credited" in line:
            count += 1
            line_items[count] = []
        elif "View Complete Trail" in line:
            break
        if count > 0:
            line_items[count].append(words)

    # crude table extraction
    items = []
    for _, y in line_items.items():
        try:
            items.append(
                {
                    "ComplaintDate": y[0][7] + " " + y[1][8],
                    "Account_No": y[0][3],
                    "Amount": y[4][3],
                    "Region": y[0][-1],
                    "UTR_No": y[0][4],
                    "UTR_Amount": y[1][6],
                    "Transaction_Date": y[0][6] + " " + y[1][7],
                }
            )
        except Exception:
            continue

    cyber_data["LineItems"] = items
    return cyber_data


def extract_month_from_string(mail_date_str):
    try:
        dt = datetime.strptime(mail_date_str.replace(" GMT", ""), "%A, %B %d, %Y %I:%M:%S %p")
        return dt.strftime("%B"), dt.month
    except Exception:
        return None, None


def calculate_ageing_days(date_str):
    try:
        dt = datetime.strptime(date_str.replace(":PM", "").replace(":AM", ""), "%d/%m/%Y %H:%M")
        return (datetime.now().date() - dt.date()).days
    except Exception:
        return None


# # ─────────────── Pipeline ─────────────── #
# def process_gmail_pdfs(updated_by_username=None):
#     decrypted_paths = fetch_and_decrypt_pdfs()
#     if not decrypted_paths:
#         print("⚠️ No decrypted PDFs")
#         return

#     user = None
#     if updated_by_username:
#         try:
#             user = User.objects.get(username=updated_by_username)
#         except User.DoesNotExist:
#             print(f"⚠️ User {updated_by_username} not found")

#     for pdf_path in decrypted_paths:
#         data = extract_structured_data_from_pdf(pdf_path)
#         line_items = data.get("LineItems", [])
#         month_name, _ = extract_month_from_string(data.get("MailDate", ""))

#         with open(pdf_path, "rb") as f_pdf:
#             file_content = ContentFile(f_pdf.read())
#             saved_pdf = default_storage.save("uploaded_pdfs/" + pdf_path.name, file_content)

#         for item in line_items:
#             report = CyberCellReport(
#                 complaint_date=item.get("ComplaintDate", ""),
#                 mail_date=data.get("MailDate", ""),
#                 mail_month=month_name,
#                 amount=item.get("Amount", ""),
#                 reference_number=data.get("RefNo", ""),
#                 police_station_address=data.get("Police_Station_Address", ""),
#                 account_number=item.get("Account_No", ""),
#                 name=data.get("Name", ""),
#                 mobile_number=(data.get("Mobile") or [""])[0],
#                 email_id=data.get("Email", ""),
#                 ageing_days=calculate_ageing_days(item.get("ComplaintDate", "")),
#                 debit_from_bank="no",
#                 region=item.get("Region", ""),
#                 utr_number=item.get("UTR_No", ""),
#                 utr_amount=item.get("UTR_Amount", ""),
#                 transaction_datetime=item.get("Transaction_Date", ""),
#                 total_fraudulent_amount=data.get("Total_Fraudulent_Amount", ""),
#                 updated_by=user,
#             )
#             report.pdf_file.name = saved_pdf
#             report.save()
#         print(f"✅ Processed {pdf_path}")





from django.db import IntegrityError, transaction

# ─────────────── Pipeline ─────────────── #
def process_gmail_pdfs(updated_by_username=None):
    decrypted_paths = fetch_and_decrypt_pdfs()
    if not decrypted_paths:
        print("⚠️ No decrypted PDFs")
        return

    user = None
    if updated_by_username:
        try:
            user = User.objects.get(username=updated_by_username)
        except User.DoesNotExist:
            print(f"⚠️ User {updated_by_username} not found")

    for pdf_path in decrypted_paths:
        data = extract_structured_data_from_pdf(pdf_path)
        line_items = data.get("LineItems", [])
        month_name, _ = extract_month_from_string(data.get("MailDate", ""))

        with open(pdf_path, "rb") as f_pdf:
            file_content = ContentFile(f_pdf.read())
            saved_pdf = default_storage.save("uploaded_pdfs/" + pdf_path.name, file_content)

        for item in line_items:
            try:
                with transaction.atomic():  # ensure rollback on failure
                    report = CyberCellReport(
                        complaint_date=item.get("ComplaintDate", ""),
                        mail_date=data.get("MailDate", ""),
                        mail_month=month_name,
                        amount=item.get("Amount", ""),
                        reference_number=data.get("RefNo", ""),
                        police_station_address=data.get("Police_Station_Address", ""),
                        account_number=item.get("Account_No", ""),
                        name=data.get("Name", ""),
                        mobile_number=(data.get("Mobile") or [""])[0],
                        email_id=data.get("Email", ""),
                        ageing_days=calculate_ageing_days(item.get("ComplaintDate", "")),
                        debit_from_bank="no",
                        region=item.get("Region", ""),
                        utr_number=item.get("UTR_No", ""),
                        utr_amount=item.get("UTR_Amount", ""),
                        transaction_datetime=item.get("Transaction_Date", ""),
                        total_fraudulent_amount=data.get("Total_Fraudulent_Amount", ""),
                        updated_by=user,
                    )
                    report.pdf_file.name = saved_pdf
                    report.save()
            except IntegrityError as e:
                # handle duplicates / constraint violations gracefully
                print(f"⚠️ Skipping duplicate for RefNo {data.get('RefNo', '')} | Error: {e}")
                continue

        print(f"✅ Processed {pdf_path}")
