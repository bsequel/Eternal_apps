from __future__ import print_function
import os
import re
import json
import base64
import pdfplumber
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from . models import *
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django.contrib.auth import get_user_model
from django.conf import settings
from pathlib import Path
import os
from django.db import IntegrityError, transaction


User = get_user_model()
# ──────────────── Load Environment Variables ──────────────── #
load_dotenv()
PDF_PASSWORD = "Zomato@123"

# Gmail API Configuration
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
# TOKEN_FILE = "token.json"

TOKEN_FILE = settings.GOOGLE_TOKEN_PATH

CREDENTIALS_FILE = settings.GOOGLE_CREDENTIALS_PATH


SUBJECT_KEYWORD = "NCRP MHA Acknowledgement No"

# ──────────────── Base Directories ──────────────── #
# BASE_DIR = Path("cyber_data")


# ──────────────── Base Directories ──────────────── #
BASE_DIR = settings.BASE_DIR / "cyber_data"
SOURCE_DIR = BASE_DIR / "EMAIL_PDFS"
DECRYPTED_DIR = BASE_DIR / "DECRYPTED_PDFS"
JSON_OUTPUT_DIR = BASE_DIR / "JSON_DATA"


os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

# ──────────────── Gmail API Authentication ──────────────── #


def save_tokens(creds):
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_tokens():
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
        if creds and creds.valid:
            if not all(scope in creds.scopes for scope in SCOPES):
                print(
                    "⚠️  Saved credentials have insufficient scopes. Re-authenticating...")
                creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and all(scope in creds.scopes for scope in SCOPES):
            creds.refresh(Request())
            save_tokens(creds)
        else:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
                print("🗑️  Removed old token file")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            save_tokens(creds)
    return creds

# ──────────────── Utility Functions ──────────────── #


def extract_ack_no(subject):
    match = re.search(
        r"Acknowledgement No[.\- ]*\s*(\d+)", subject, re.IGNORECASE)
    return match.group(1) if match else None


def remove_pdf_password(input_path, output_path, password):
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            if password is None:
                print(
                    f"❌ No password provided for encrypted PDF: {input_path}")
                return False
            result = reader.decrypt(password)
            if result == 0:
                print(f"❌ Incorrect password for: {input_path}")
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
        message = service.users().messages().get(userId='me', id=message_id).execute()
        parts = message['payload'].get('parts', [message['payload']])
        for part in parts:
            if part.get('filename'):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=message_id, id=attachment_id
                    ).execute()
                    data = attachment['data']
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    attachments.append({
                        'filename': part['filename'],
                        'data': file_data
                    })
    except Exception as e:
        print(f"❌ Error getting attachments: {e}")
    return attachments


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
            message = service.users().messages().get(
                userId="me", id=msg["id"]).execute()
            headers = message["payload"].get("headers", [])
            subject = next((h["value"]
                           for h in headers if h["name"] == "Subject"), "")

            if SUBJECT_KEYWORD.lower() not in subject.lower():
                continue

            ack_no = extract_ack_no(subject)
            if not ack_no:
                continue

            attachments = get_message_attachments(service, msg["id"])
            for idx, att in enumerate(attachments, start=1):
                ext = os.path.splitext(att["filename"])[1] or ".pdf"
                raw_path = SOURCE_DIR / f"{ack_no}_{idx}{ext}"
                dec_path = DECRYPTED_DIR / f"{ack_no}_{idx}{ext}"
                with open(raw_path, "wb") as f:
                    f.write(att["data"])
                print(f"📥 Downloaded: {raw_path}")
                if remove_pdf_password(raw_path, dec_path, PDF_PASSWORD):
                    decrypted_paths.append(dec_path)

            try:
                service.users().messages().modify(
                    userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            except Exception as e:
                print(f"⚠️ Could not mark as read: {e}")

    except Exception as e:
        print(f"❌ Gmail API Error: {e}")
    # print(decrypted_paths)  

    return decrypted_paths

# ──────────────── Data Extraction ──────────────── #


def extract_structured_data_from_pdf(pdf_path, output_json_path=None):
    pdf_path = Path(pdf_path)
    if output_json_path is None:
        output_json_path = JSON_OUTPUT_DIR / (pdf_path.stem + ".json")

    def extract_text_lines(path):
        with pdfplumber.open(path) as pdf:
            all_text = "\n".join(page.extract_text()
                                 or "" for page in pdf.pages)
        return [line.strip() for line in all_text.split('\n') if line.strip()]

    def is_valid(text):
        return bool(re.fullmatch(r'[a-zA-Z0-9 ]+', text))

    def extract_datetime(text):
        pattern = (
            r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),"
            r"\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM)\s+GMT\b"
        )
        match = re.search(pattern, text)
        return match.group() if match else None

    lines = extract_text_lines(pdf_path)
    cyber_data = {}
    line_items = {}
    count = 0
    line_no = 0

    for line in lines:
        words = line.split()
        if "Sent:" in line:
            cyber_data["MailDate"] = extract_datetime(line)
        elif "Mobile" in line and words:
            cyber_data.setdefault("Mobile", []).append(words[-1])
        elif "Email" in line and '@' in line and words:
            cyber_data["Email"] = words[-1]
        elif "Address" in line and words:
            cyber_data["Address"] = " ".join(words[1:])
        elif "State /District /Police Station" in line:
            cyber_data["Police_Station_Address"] = line.split(
                "State /District /Police Station")[-1].strip()
        elif "Acknowledgement No." in line and words:
            cyber_data["RefNo"] = words[-1]
        elif "Name" in line and is_valid(line):
            if len(line.split()) in (2, 3):
                cyber_data["Name"] = line.split("Name")[-1].strip()
        elif "Total Fraudulent Amount reported by complainant" in line:
            parts = line.split(':', 1)
            if len(parts) > 1:
                cyber_data["Total_Fraudulent_Amount"] = parts[1].strip()
        elif "Account Credited" in line:
            count += 1
            line_no = count
        elif "View Complete Trail" in line:
            break
        if line_no > 0:
            line_items.setdefault(line_no, []).append(words)

    line_items_list = []
    for _, y in line_items.items():
        try:
            single_line = " ".join(item for sublist in y for item in sublist)
            # match_ = re.search(
            #     r":\s+(\d+)\s+([A-Za-z0-9]+)", single_line, re.IGNORECASE)
            # if match_:
            #     account_no = match_.group(1)
            #     utr_or_remark = match_.group(2)
            m = re.search(r"(?si)(Account Credited.*?)(?=Transaction)", single_line)
            print(m.group(1),"----")
            if m:
                acc_ref = m.group(1).split()
                account_no  = acc_ref[-2]
                utr_or_remark  = acc_ref[-1]
                
            date_time_pairs = [f"{d.replace('/', '-')} {t}" for d, t in zip(
                re.findall(r"\d{2}/\d{2}/\d{4}", single_line),
                re.findall(r"\d{1,2}:\d{2}:(?:AM|PM)",
                           single_line, re.IGNORECASE)
            )]
            line_dict = {
                'ComplaintDate': date_time_pairs[1] if len(date_time_pairs) > 1 else None,
                'Account_No': account_no,
                'Amount': y[4][3] if len(y) > 4 and len(y[4]) > 3 else None,
                'Region': y[0][-1],
                'UTR_No': utr_or_remark,
                'UTR_Amount': y[1][6] if len(y) > 1 and len(y[1]) > 6 else None,
                'Transaction_Date': date_time_pairs[2] if len(date_time_pairs) > 2 else None
            }
            # line_dict = {
            #     'ComplaintDate': date_time_pairs[1].split(" ")[0],
            #     'Account_No': account_no,
            #     'Amount': y[4][3],
            #     'Region': y[0][-1],
            #     'UTR_No': utr_or_remark,
            #     'UTR_Amount': y[1][6],
            #     'Transaction_Date': date_time_pairs[2]
            # }
            line_items_list.append(line_dict)
        except Exception:
            continue

    cyber_data["LineItems"] = line_items_list
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(cyber_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Structured data saved to: {output_json_path}")
    return output_json_path

# ──────────────── Callable Function ──────────────── #


# -------------------- db insert  ----------------------

def extract_month_from_string(mail_date_str):
    try:
        dt = datetime.strptime(mail_date_str.replace(" GMT", ""), "%A, %B %d, %Y %I:%M:%S %p")
        return dt.strftime("%B"), dt.month
    except Exception:
        return None, None


def calculate_ageing_days(date_str):
    try:
        dt = datetime.strptime(date_str.replace(":PM", "").replace(":AM", ""), "%d-%m-%Y %H:%M")
        return (datetime.now().date() - dt.date()).days
    except Exception:
        return None
    





# # -------------------- db insert  ----------------------
import re
from datetime import datetime

def extract_ack_no(subject):
    match = re.search(r"Acknowledgement No[.\- ]*\s*(\d+)", subject, re.IGNORECASE)
    return match.group(1) if match else None



    


from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def extract_and_insert_data_from_pdf(output_pdf: str, updated_by_username: str = None):
    try:
        print(f"Processing PDF: {output_pdf}, updated_by_username: {updated_by_username}")

        json_path = extract_structured_data_from_pdf(output_pdf)
        print(f"JSON saved at: {json_path}")

        with open(json_path, "r", encoding="utf-8") as file:
            records = json.load(file)
        line_items = records.get('LineItems', [])
        month_name, _ = extract_month_from_string(records.get('MailDate', ''))

        user = None
        if updated_by_username:
            try:
                user = User.objects.get(username=updated_by_username)
            except User.DoesNotExist:
                print(f"User '{updated_by_username}' not found. Proceeding without updated_by.")

        # --- NEW: Save the PDF file ONCE using storage system ---
        with open(output_pdf, 'rb') as f_pdf:
            file_content = ContentFile(f_pdf.read())
            pdf_file_name = 'uploaded_pdfs/' + os.path.basename(output_pdf)
            saved_pdf_path = default_storage.save(pdf_file_name, file_content)

        # For every entry, create a report but just set the file path
        for item in line_items:
            print("Inserting:", item)
            report = CyberCellReport(
                complaint_date=item.get("ComplaintDate", ""),
                mail_date=records.get("MailDate", ""),
                mail_month=month_name,
                amount=item.get("Amount", ""),
                reference_number=records.get("RefNo", ""),
                police_station_address=records.get("Police_Station_Address", ""),
                account_number=item.get("Account_No", ""),
                name=records.get("Name", ""),
                mobile_number=records.get("Mobile", [""])[0],
                email_id=records.get("Email", ""),
                ageing_days=calculate_ageing_days(item.get("ComplaintDate", "")),
                debit_from_bank='no',  # default
                region=item.get("Region", ""),
                utr_number=item.get("UTR_No", ""),
                utr_amount=item.get("UTR_Amount", ""),
                transaction_datetime=item.get("Transaction_Date", ""),
                total_fraudulent_amount=records.get("Total_Fraudulent_Amount", ""),
                updated_by=user,  # optional
            )
            # Reference the already saved PDF path
            report.pdf_file.name = saved_pdf_path
            report.save()
        print("✅ All records inserted successfully.")

    except Exception as e:
        print("Error:", e)    

def main():
    
    pdfs = fetch_and_decrypt_pdfs()
    for pdf in pdfs:
       extract_and_insert_data_from_pdf(pdf)
    
    


def check_unread_mails():
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        query = f'is:unread subject:"{SUBJECT_KEYWORD}"'
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        return len(messages)  # returns count of unread mails
    except Exception as e:
        print(f"❌ Gmail API Error: {e}")
        return 0


# # ──────────────── Script Entry Point ──────────────── #
# if __name__ == "__main__":
#     count = check_unread_mails()
#     if count == 0:
#         print("📭 No unread mails")
#     else:
#         print(f"📧 You have {count} unread mails")
#         main()
