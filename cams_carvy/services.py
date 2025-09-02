import base64
import os
from pathlib import Path
from dotenv import load_dotenv
import zipfile
import requests
import re
import sys
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import json

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


from django.conf import settings
# Load environment
# env_path = Path('.') / '.env'
load_dotenv()

# Configuration
SUBJECT_LINE = "CAMS Mailback"
CAMS_FOLDER = "cams_gmail_data"
PROCESSED_FILE = "processed_emails.txt"
PDF_DATA_FOLDER = "pdf_extracted_data"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# File paths
TOKEN_FILE = settings.GOOGLE_TOKEN_PATH
CREDENTIALS_FILE = "credentials.json"

# HARDCODED PASSWORDS ONLY
HARDCODED_PASSWORDS = [
    os.getenv('FILE_PASSWORD', ''),
    ''  # Try no password first
]

def save_tokens(creds: Credentials):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

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
        else:
            if os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
                save_tokens(creds)
    return creds

def load_processed_emails():
    """Load list of already processed email IDs"""
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(line.strip() for line in f)
    except:
        pass
    return set()

def save_processed_email(email_id):
    """Save email ID as processed"""
    try:
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{email_id}\n")
    except Exception as e:
        print(f"Error saving processed email ID: {e}")

def extract_zip(zip_path, zip_filename):
    """Extract zip file with hardcoded passwords only"""
    for password in HARDCODED_PASSWORDS:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if password:
                    zip_ref.extractall(CAMS_FOLDER, pwd=password.encode('utf-8'))
                    print(f"✓ Extracted {zip_filename} with password")
                else:
                    zip_ref.extractall(CAMS_FOLDER)
                    print(f"✓ Extracted {zip_filename} (no password)")
                
                for file in zip_ref.namelist():
                    print(f"  - {file}")
                return
        except:
            continue
    
    print(f"✗ Could not extract {zip_filename} with available passwords")

def extract_current_valuation(zip_path, zip_filename):
    """Extract only 'current valuation' file from zip"""
    for password in HARDCODED_PASSWORDS:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test password
                if password:
                    test_file = zip_ref.namelist()[0]
                    zip_ref.read(test_file, pwd=password.encode('utf-8'))
                
                # Find current valuation file
                current_val_file = None
                for file in zip_ref.namelist():
                    if 'current' in file.lower() and 'valuation' in file.lower():
                        current_val_file = file
                        break
                
                if current_val_file:
                    if password:
                        zip_ref.extract(current_val_file, CAMS_FOLDER, pwd=password.encode('utf-8'))
                    else:
                        zip_ref.extract(current_val_file, CAMS_FOLDER)
                    print(f"✓ Extracted: {current_val_file}")
                    
                    # Move to main folder if in subfolder
                    extracted_path = os.path.join(CAMS_FOLDER, current_val_file)
                    if os.path.dirname(current_val_file):
                        new_path = os.path.join(CAMS_FOLDER, os.path.basename(current_val_file))
                        os.rename(extracted_path, new_path)
                        try:
                            os.rmdir(os.path.dirname(extracted_path))
                        except:
                            pass
                else:
                    # Extract all if current valuation not found
                    if password:
                        zip_ref.extractall(CAMS_FOLDER, pwd=password.encode('utf-8'))
                    else:
                        zip_ref.extractall(CAMS_FOLDER)
                    print(f"✓ Extracted all files from {zip_filename}")
                return
        except:
            continue
    
    print(f"✗ Could not extract {zip_filename} with available passwords")

def remove_pdf_password(pdf_path):
    """Remove password from PDF file"""
    try:
        reader = PdfReader(pdf_path)
        
        if not reader.is_encrypted:
            print(f"✓ PDF {os.path.basename(pdf_path)} not encrypted")
            return pdf_path
        
        # Try to decrypt
        for password in HARDCODED_PASSWORDS:
            try:
                if reader.decrypt(password):
                    base_name = os.path.splitext(pdf_path)[0]
                    output_path = f"{base_name}_unlocked.pdf"
                    
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    print(f"✓ Created unlocked PDF: {os.path.basename(output_path)}")
                    os.remove(pdf_path)  # Remove encrypted version
                    return output_path
            except:
                continue
        
        print(f"✗ Could not unlock PDF {os.path.basename(pdf_path)} - deleting")
        os.remove(pdf_path)
        return None
        
    except Exception as e:
        print(f"Error with PDF {os.path.basename(pdf_path)}: {e}")
        try:
            os.remove(pdf_path)
        except:
            pass
        return None

def extract_pdf_data(pdf_path):
    """Extract data from PDF using pdfplumber"""
    try:
        os.makedirs(PDF_DATA_FOLDER, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = os.path.join(PDF_DATA_FOLDER, f"{base_name}_extracted.txt")
        
        extracted_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processing PDF: {os.path.basename(pdf_path)} ({len(pdf.pages)} pages)")
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    extracted_data.append(f"=== PAGE {page_num} ===\n")
                    extracted_data.append(text)
                    extracted_data.append("\n" + "="*50 + "\n")
                
                tables = page.extract_tables()
                if tables:
                    extracted_data.append(f"\n=== TABLES FROM PAGE {page_num} ===\n")
                    for table_num, table in enumerate(tables, 1):
                        extracted_data.append(f"\nTable {table_num}:\n")
                        for row in table:
                            if row:
                                row_data = [str(cell) if cell is not None else "" for cell in row]
                                extracted_data.append(" | ".join(row_data) + "\n")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(extracted_data)
        
        print(f"✓ PDF data extracted to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error extracting PDF data: {e}")
        return None

def process_pdf_files():
    """Process all PDF files in CAMS folder"""
    if not os.path.exists(CAMS_FOLDER):
        return
        
    pdf_files = [f for f in os.listdir(CAMS_FOLDER) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(CAMS_FOLDER, pdf_file)
        print(f"\nProcessing PDF: {pdf_file}")
        
        unlocked_pdf_path = remove_pdf_password(pdf_path)
        if unlocked_pdf_path:
            extract_pdf_data(unlocked_pdf_path)

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

def extract_message_body_from_payload(payload):
    """Extract message body from Gmail API payload"""
    body = ""
    try:
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] in ['text/plain', 'text/html'] and part.get('body', {}).get('data'):
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        else:
            if payload['mimeType'] in ['text/plain', 'text/html'] and payload.get('body', {}).get('data'):
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error extracting message body: {e}")
    
    return body

def download_cams_zip(url):
    """Download CAMS zip file"""
    try:
        print(f"Downloading CAMS file from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        filename = url.split('fname=')[1].split('&')[0] if 'fname=' in url else f"cams_{abs(hash(url)) % 10000}.zip"
        if not filename.endswith('.zip'):
            filename += '.zip'
        
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        filepath = os.path.join(CAMS_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved CAMS zip: {filename}")
        extract_current_valuation(filepath, filename)
        
        # Delete zip file
        try:
            os.remove(filepath)
            print(f"Deleted zip file: {filename}")
        except:
            pass
                
    except Exception as e:
        print(f"Error downloading CAMS file: {e}")

def download_zip_from_body(body):
    """Extract and download CAMS links from email body"""
    if not body:
        return
    
    cams_pattern = r'https://old\.camsonline\.com/dnldresult\.asp\?fname=[^"\s<>]+'
    cams_urls = re.findall(cams_pattern, body, re.IGNORECASE)
    
    print(f"Found {len(cams_urls)} CAMS download links")
    
    for url in cams_urls:
        download_cams_zip(url)

def download_attachments_with_google_api(subject_filter):
    """Download attachments from emails using Google API"""
    os.makedirs(CAMS_FOLDER, exist_ok=True)
    
    processed_emails = load_processed_emails()
    
    try:
        creds = get_credentials()
        if not creds:
            print("❌ Failed to get credentials")
            return
            
        service = build("gmail", "v1", credentials=creds)
        query = f'subject:"{subject_filter}"'
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        
        if not messages:
            print(f'No messages found with subject: {subject_filter}')
            return
        
        new_messages = [msg for msg in messages if msg['id'] not in processed_emails]
        
        if not new_messages:
            print('No new messages to process')
            return
            
        print(f'Found {len(new_messages)} new messages')
        
        for message in new_messages:
            try:
                # Get message details
                msg_data = service.users().messages().get(userId="me", id=message["id"]).execute()
                
                headers = msg_data.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                print(f"Processing: {subject}")
                
                payload = msg_data.get('payload', {})
                
                # Extract body and download CAMS links
                body = extract_message_body_from_payload(payload)
                download_zip_from_body(body)
                
                # Download attachments
                attachments = get_message_attachments(service, message["id"])
                for att in attachments:
                    filename = "".join(c for c in att["filename"] if c.isalnum() or c in "._-")
                    filepath = os.path.join(CAMS_FOLDER, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(att["data"])
                    print(f"📥 Downloaded: {filename}")
                    
                    if filename.lower().endswith('.zip'):
                        extract_zip(filepath, filename)
                
                save_processed_email(message['id'])
                
            except Exception as e:
                print(f"❌ Error processing message {message.get('id', 'unknown')}: {e}")
                continue
            
    except Exception as error:
        print(f'❌ Gmail API error: {error}')

# def main():
#     print("Starting Gmail CAMS Processor with Google API...")
    
#     try:
#         download_attachments_with_google_api(SUBJECT_LINE)
#         print(f"All attachments saved to '{CAMS_FOLDER}' folder")
        
#         print("\nProcessing PDF files...")
#         process_pdf_files()
        
#         print("\nProcessing completed!")
        
#     except Exception as e:
#         print(f"Error: {e}")
#         sys.exit(1)

# if __name__ == '__main__':
#     main()
def process_cams_emails():
    try:
        download_attachments_with_google_api(SUBJECT_LINE)
        print(f"All attachments saved to '{CAMS_FOLDER}' folder")
        
        print("\nProcessing PDF files...")
        process_pdf_files()
        
        print("\nProcessing completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)



# =================================   extraction part  =================================================


import shutil
from email.header import decode_header
import json
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
import sys
import requests
import zipfile
from dotenv import load_dotenv
import base64
import imaplib
import email
from .models import CamsPortfolio  # adjust your import path
from django.db import transaction
import pandas as pd
import os
import re
from pathlib import Path
from decimal import Decimal
from django.utils.dateparse import parse_date
from .models import CAMSTransaction, CAMSSummary
from datetime import datetime
from django.db import IntegrityError


from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pandas as pd
import pytz
import re
from django.db.utils import IntegrityError
import pandas as pd
from django.db import IntegrityError




def parse_summary_line(line: str) -> dict:
    """Extract key:value metrics from summary lines."""
    pairs = re.findall(
        r'([^:|]+):\s*(?:INR|₹)?\s*([-]?\d[\d,]*(?:\.\d+)?)', line)
    result = {}
    for key, val in pairs:
        key = re.sub(r"\s+on\s+\d{1,2}-[A-Za-z]{3}-\d{4}", "", key).strip()
        result[key] = Decimal(val.replace(",", "").strip())
    return result







def process_cams_files(folder="pdf_extracted_data") -> dict:
    """
    Parses CAS text files inside folder and inserts into Django DB models.
    Handles stamp duty for purchases.
    Tracks Inserted/Duplicate.
    Saves transactions + summaries to Excel with 2 sheets.
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        return {"error": f"Folder '{folder}' not found."}

    txt_files = list(folder_path.glob("CAS*.txt"))
    if not txt_files:
        return {"error": "No CAS text files found."}

    limited_variants = [
        "Ltd", "Ltd.", "LTD", "LTD.", "Limited", "LIMITED",
        "ltd", "ltd.", "limited", "Limited Company",
        "LIMITED COMPANY", "Ltd Company", "LTD COMPANY"
    ]

    tx_count = sm_count = tx_dup_count = sm_dup_count = 0
    excel_transactions = []
    excel_summaries = []

    for txt_file in txt_files:
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.readlines()

        curr_amc = curr_entity = curr_folio = curr_isin = curr_scheme = None
        last_purchase = {}

        for line in content:
            parts = line.split()

            # --- AMC ---
            if line.strip().endswith("Mutual Fund"):
                curr_amc = line.strip()
                curr_entity = curr_folio = curr_isin = curr_scheme = None
                continue

            if curr_amc:
                # --- Entity Name ---
                if parts and parts[-1] in limited_variants:
                    curr_entity = line.strip()

                # --- Folio Number ---
                folio_match = re.search(r'Folio No:\s*([A-Za-z0-9/]+)', line)
                if folio_match:
                    curr_folio = folio_match.group(1).strip()

                # --- Scheme + ISIN ---
                match = re.match(r"^(.*?)\s*-\s*ISIN:\s*([A-Z0-9]+)", line)
                if match:
                    scheme, isin = match.groups()
                    curr_isin = isin.strip()
                    curr_scheme = scheme.strip()

                # --- Transaction Processing ---
                if curr_entity and curr_folio and curr_isin and curr_scheme:
                    txn_match = re.match(r'^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)', line)
                    if txn_match:
                        txn_date = datetime.strptime(txn_match.group(1), "%d-%b-%Y").date()

                        desc_pattern = r"\d{2}-[A-Za-z]{3}-\d{4}\s+(.*?)(?=\s+\(|\s+\d{1,3}(?:,\d{3})*\.\d{2})"
                        desc_match = re.search(desc_pattern, line)
                        desc = desc_match.group(1).strip() if desc_match else None

                        val_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,4}|\d+\.\d{2,4}"
                        values = re.findall(val_pattern, line)

                        txn_value = Decimal(values[0].replace(",", "")) if len(values) > 0 else None
                        txn_units = Decimal(values[1].replace(",", "")) if len(values) > 1 else None
                        txn_nav = Decimal(values[2].replace(",", "")) if len(values) > 2 else None
                        txn_unitbal = Decimal(values[3].replace(",", "")) if len(values) > 3 else None

                        if desc:
                            # --- Stamp duty logic ---
                            if "purchase" in desc.lower():
                                last_purchase = {
                                    "entity_name": curr_entity,
                                    "amc_name": curr_amc,
                                    "folio_number": curr_folio,
                                    "isin": curr_isin,
                                    "scheme_name": curr_scheme,
                                    "transaction_date": txn_date,
                                    "transaction_description": desc,
                                    "value": txn_value,
                                    "stamp_duty": None,
                                    "units": txn_units,
                                    "nav": txn_nav,
                                    "unit_balance": txn_unitbal
                                }
                                continue

                            elif "stamp" in desc.lower() and last_purchase:
                                last_purchase["stamp_duty"] = txn_value
                                tx_obj = CAMSTransaction(**last_purchase)
                                try:
                                    tx_obj.save()
                                    tx_count += 1
                                    status = "Inserted"
                                except IntegrityError:
                                    tx_dup_count += 1
                                    status = "Duplicate"
                                excel_transactions.append({**last_purchase, "status": status})
                                last_purchase = {}
                                continue

                            else:
                                tx_obj = CAMSTransaction(
                                    entity_name=curr_entity,
                                    amc_name=curr_amc,
                                    folio_number=curr_folio,
                                    isin=curr_isin,
                                    scheme_name=curr_scheme,
                                    transaction_date=txn_date,
                                    transaction_description=desc,
                                    value=txn_value,
                                    stamp_duty=Decimal(0.00),
                                    units=txn_units,
                                    nav=txn_nav,
                                    unit_balance=txn_unitbal
                                )
                                try:
                                    tx_obj.save()
                                    tx_count += 1
                                    status = "Inserted"
                                except IntegrityError:
                                    tx_dup_count += 1
                                    status = "Duplicate"
                                excel_transactions.append({
                                    "entity_name": curr_entity,
                                    "amc_name": curr_amc,
                                    "folio_number": curr_folio,
                                    "isin": curr_isin,
                                    "scheme_name": curr_scheme,
                                    "transaction_date": txn_date,
                                    "transaction_description": desc,
                                    "value": txn_value,
                                    "stamp_duty": Decimal(0.00),
                                    "units": txn_units,
                                    "nav": txn_nav,
                                    "unit_balance": txn_unitbal,
                                    "status": status
                                })

                # --- Summary Processing ---
                if curr_entity and curr_folio and curr_isin and curr_scheme:
                    if "closing unit balance" in line.lower():
                        nav_date_match = re.search(r'NAV on (\d{1,2}-[A-Za-z]{3}-\d{4})', line)
                        parsed_date = datetime.strptime(nav_date_match.group(1), "%d-%b-%Y").date() if nav_date_match else None

                        summary = parse_summary_line(line)
                        summary_obj = CAMSSummary(
                            entity_name=curr_entity,
                            amc_name=curr_amc,
                            folio_number=curr_folio,
                            isin=curr_isin,
                            scheme_name=curr_scheme,
                            closing_unit_balance=summary.get("Closing Unit Balance") or 0.00,
                            nav=summary.get("NAV") or 0.00,
                            total_cost_value=summary.get("Total Cost Value") or 0.00,
                            market_value=summary.get("Market Value") or 0.00,
                            nav_date=parsed_date
                        )
                        try:
                            summary_obj.save()
                            sm_count += 1
                            status = "Inserted"
                        except IntegrityError:
                            sm_dup_count += 1
                            status = "Duplicate"
                        excel_summaries.append({
                            "entity_name": curr_entity,
                            "amc_name": curr_amc,
                            "folio_number": curr_folio,
                            "isin": curr_isin,
                            "scheme_name": curr_scheme,
                            "closing_unit_balance": summary.get("Closing Unit Balance") or 0.00,
                            "nav": summary.get("NAV") or 0.00,
                            "total_cost_value": summary.get("Total Cost Value") or 0.00,
                            "market_value": summary.get("Market Value") or 0.00,
                            "nav_date": parsed_date,
                            "status": status
                        })

    # --- Save Excel with 2 sheets ---
    timestamp_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d-%m-%Y_%H%M%S')
    output_file = folder_path / f"cams_report_{timestamp_str}.xlsx"
    # output_file = folder_path / "cams_report.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        if excel_transactions:
            pd.DataFrame(excel_transactions).to_excel(writer, sheet_name="Transactions", index=False)
        if excel_summaries:
            pd.DataFrame(excel_summaries).to_excel(writer, sheet_name="Summaries", index=False)

    # --- Timestamps ---
    utc_now = datetime.now(pytz.utc).strftime('%d-%m-%Y %H:%M:%S')
    ist_now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d-%m-%Y %H:%M:%S')

    return {
        "transactions_inserted": tx_count,
        "transactions_duplicates": tx_dup_count,
        "summaries_inserted": sm_count,
        "summaries_duplicates": sm_dup_count,
        "excel_report": str(output_file),
        "timestamp_utc": utc_now,
        "timestamp_ist": ist_now,
        "message": "✅ CAM parsing completed"
    }






# =========================   old working  =====================================

# def process_cams_files(folder="pdf_extracted_data") -> dict:
#     """
#     Parses CAS text files inside folder and inserts into Django DB models.
#     Returns summary dict with counts.
#     """
#     folder_path = Path(folder)
#     if not folder_path.exists():
#         return {"error": f"Folder '{folder}' not found."}

#     txt_files = list(folder_path.glob("CAS*.txt"))
#     if not txt_files:
#         return {"error": "No CAS text files found."}

#     limited_variants = [
#         "Ltd", "Ltd.", "LTD", "LTD.", "Limited", "LIMITED",
#         "ltd", "ltd.", "limited", "Limited Company",
#         "LIMITED COMPANY", "Ltd Company", "LTD COMPANY"
#     ]

#     bulk_txns = []
#     bulk_summaries = []

#     for txt_file in txt_files:
#         with open(txt_file, "r", encoding="utf-8") as f:
#             content = f.readlines()

#         curr_amc = curr_entity = curr_folio = curr_isin = curr_scheme = None
#         last_purchase = {}

#         for line in content:
#             parts = line.split()

#             # --- AMC ---
#             if line.strip().endswith("Mutual Fund"):
#                 curr_amc = line.strip()
#                 curr_entity = curr_folio = curr_isin = curr_scheme = None
#                 continue

#             if curr_amc:
#                 # --- Entity Name ---
#                 if parts and parts[-1] in limited_variants:
#                     curr_entity = line.strip()

#                 # --- Folio Number ---
#                 folio_match = re.search(r'Folio No:\s*([A-Za-z0-9/]+)', line)
#                 if folio_match:
#                     curr_folio = folio_match.group(1).strip()

#                 # --- Scheme + ISIN ---
#                 match = re.match(r"^(.*?)\s*-\s*ISIN:\s*([A-Z0-9]+)", line)
#                 if match:
#                     scheme, isin = match.groups()
#                     curr_isin = isin.strip()
#                     curr_scheme = scheme.strip()

#                 # --- Transaction Processing ---
#                 if curr_entity and curr_folio and curr_isin and curr_scheme:
#                     txn_match = re.match(
#                         r'^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)', line)
#                     if txn_match:

#                         txn_date = txn_match.group(1)
#                         txn_date = datetime.strptime(
#                             txn_date, "%d-%b-%Y").date()

#                         # print(txn_date,"jjjjj",txn_match.group(1))
#                         desc_pattern = r"\d{2}-[A-Za-z]{3}-\d{4}\s+(.*?)(?=\s+\(|\s+\d{1,3}(?:,\d{3})*\.\d{2})"
#                         desc_match = re.search(desc_pattern, line)
#                         desc = desc_match.group(
#                             1).strip() if desc_match else None

#                         val_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,4}|\d+\.\d{2,4}"
#                         values = re.findall(val_pattern, line)

#                         txn_value = Decimal(values[0].replace(
#                             ",", "")) if len(values) > 0 else None
#                         txn_units = Decimal(values[1].replace(
#                             ",", "")) if len(values) > 1 else None
#                         txn_nav = Decimal(values[2].replace(
#                             ",", "")) if len(values) > 2 else None
#                         txn_unitbal = Decimal(values[3].replace(
#                             ",", "")) if len(values) > 3 else None

#                         if desc:
#                             if "purchase" in desc.lower():
#                                 last_purchase = dict(
#                                     entity_name=curr_entity,
#                                     amc_name=curr_amc,
#                                     folio_number=curr_folio,
#                                     isin=curr_isin,
#                                     scheme_name=curr_scheme,
#                                     transaction_date=txn_date,
#                                     transaction_description=desc,
#                                     value=txn_value,
#                                     stamp_duty=None,
#                                     units=txn_units,
#                                     nav=txn_nav,
#                                     unit_balance=txn_unitbal,
#                                 )
#                             elif "stamp" in desc.lower():
#                                 if last_purchase:
#                                     last_purchase["stamp_duty"] = txn_value
#                                     bulk_txns.append(
#                                         CAMSTransaction(**last_purchase))
#                                     last_purchase = {}
#                             else:
#                                 bulk_txns.append(
#                                     CAMSTransaction(
#                                         entity_name=curr_entity,
#                                         amc_name=curr_amc,
#                                         folio_number=curr_folio,
#                                         isin=curr_isin,
#                                         scheme_name=curr_scheme,
#                                         transaction_date=txn_date,
#                                         transaction_description=desc,
#                                         value=txn_value,
#                                         stamp_duty=0.00,
#                                         units=txn_units,
#                                         nav=txn_nav,
#                                         unit_balance=txn_unitbal,
#                                     )
#                                 )

#                 # --- Summary Processing ---
#                 if curr_entity and curr_folio and curr_isin and curr_scheme:
#                     if "closing unit balance" in line.lower():
#                         print(line)
#                         nav_date_match = re.search(r'NAV on (\d{1,2}-[A-Za-z]{3}-\d{4})', line)
#                         if nav_date_match:
#                             nav_date = nav_date_match.group(1)
#                         else: 
#                             pass
#                         parsed_date = datetime.strptime(nav_date, "%d-%b-%Y").date()
#                         summary = parse_summary_line(line)
#                         print(line,summary.get(
#                                     "Closing Unit Balance"),summary.get(
#                                     "Total Cost Value"),summary.get(
#                                     "NAV"),summary.get(
#                                     "Market Value"))
#                         bulk_summaries.append(
#                             # CAMSSummary(
#                             #     entity_name=curr_entity,
#                             #     amc_name=curr_amc,
#                             #     folio_number=curr_folio,
#                             #     isin=curr_isin,
#                             #     scheme_name=curr_scheme,
#                             #     closing_unit_balance=summary.get("Closing Unit Balance"),
#                             #     nav=summary.get("NAV"),
#                             #     total_cost_value=summary.get("Total Cost Value"),
#                             #     market_value=summary.get("Market Value"),
#                             # )
#                             CAMSSummary(
#                                 entity_name=curr_entity,
#                                 amc_name=curr_amc,
#                                 folio_number=curr_folio,
#                                 isin=curr_isin,
#                                 scheme_name=curr_scheme,
#                                 closing_unit_balance=summary.get(
#                                     "Closing Unit Balance") or 0.00,
#                                 nav=summary.get("NAV") or 0.00,
#                                 total_cost_value=summary.get(
#                                     "Total Cost Value") or 0.00,
#                                 market_value=summary.get(
#                                     "Market Value") or 0.00,
#                                 nav_date=parsed_date
#                             )

#                         )

#     # ✅ DB Insert
#     tx_count = sm_count = 0
#     if bulk_txns:
#         CAMSTransaction.objects.bulk_create(bulk_txns, ignore_conflicts=True)
#         tx_count = len(bulk_txns)
#     if bulk_summaries:
#         CAMSSummary.objects.bulk_create(bulk_summaries, ignore_conflicts=True)
#         sm_count = len(bulk_summaries)

#     return {
#         "transactions_inserted": tx_count,
#         "summaries_inserted": sm_count,
#         "message": "✅ CAS parsing completed"
#     }

# =========================   old working  =====================================

# # services.py
# from pathlib import Path
# import re
# from datetime import datetime
# from decimal import Decimal
# from .models import CAMSTransaction, CAMSSummary

# def safe_decimal(value):
#     """Convert string to Decimal safely"""
#     if not value:
#         return None
#     try:
#         return Decimal(str(value).replace(',', ''))
#     except:
#         return None

# def parse_date(date_str):
#     """Parse DD-MMM-YYYY date format"""
#     if not date_str:
#         return None
#     try:
#         return datetime.strptime(date_str, '%d-%b-%Y').date()
#     except:
#         return None

# def import_cams_data(folder="pdf_extracted_data", clear_existing=False):
#     """Main function to import CAMS data"""

#     # if clear_existing:
#     #     CAMSTransaction.objects.all().delete()
#     #     CAMSSummary.objects.all().delete()

#     folder_path = Path(folder)
#     if not folder_path.exists():
#         raise FileNotFoundError(f"Folder '{folder}' not found")

#     txt_files = list(folder_path.glob("CAS*.txt"))
#     print(txt_files)
#     if not txt_files:
#         raise FileNotFoundError("No CAS*.txt files found")

#     transaction_count = 0
#     summary_count = 0

#     for txt_file in txt_files:
#         with open(txt_file, "r", encoding="utf-8") as f:
#             lines = f.readlines()

#         # Current context
#         amc = entity = folio = isin = scheme = None
#         last_purchase = None

#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue

#             try:
#                 # Find AMC name (ends with "Mutual Fund")
#                 if line.endswith("Mutual Fund"):
#                     amc = line
#                     entity = folio = isin = scheme = None
#                     continue

#                 if not amc:
#                     continue

#                 # Find entity name (ends with Ltd/Limited variants)
#                 if any(line.endswith(variant) for variant in ["Ltd", "Ltd.", "Limited", "LIMITED"]):
#                     entity = line
#                     continue

#                 # Find folio number
#                 if line.startswith("Folio No:"):
#                     folio = re.search(r'Folio No:\s*([\w\s/]+)', line)
#                     if folio:
#                         folio = folio.group(1).strip().replace(" ", "")
#                     continue

#                 # Find ISIN and scheme
#                 isin_match = re.match(r"^(.*?)- ISIN:\s*([A-Z0-9]+)", line)
#                 if isin_match:
#                     scheme, isin = isin_match.groups()
#                     scheme = scheme.strip()
#                     isin = isin.strip()
#                     continue

#                 # Skip if we don't have complete context
#                 if not all([entity, folio, isin, scheme]):
#                     continue

#                 # Process summary line (closing unit balance)
#                 if "closing unit balance" in line.lower():
#                     numbers = re.findall(r'([\d,]+\.?\d*)', line)
#                     if len(numbers) >= 4:
#                         CAMSSummary.objects.update_or_create(
#                             folio_number=folio,
#                             isin=isin,
#                             defaults={
#                                 'entity_name': entity,
#                                 'amc_name': amc,
#                                 'scheme_name': scheme,
#                                 'closing_unit_balance': safe_decimal(numbers[0]),
#                                 'nav': safe_decimal(numbers[1]),
#                                 'total_cost_value': safe_decimal(numbers[2]),
#                                 'market_value': safe_decimal(numbers[3]),
#                             }
#                         )
#                         summary_count += 1
#                     continue

#                 # Process transaction line (starts with date)
#                 if re.match(r'^\d{2}-[A-Za-z]{3}-\d{4}', line):
#                     parts = line.split()
#                     if len(parts) < 2:
#                         continue

#                     txn_date = parts[0]
#                     desc_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}\s+(.+?)(?=\s+\d)', line)
#                     if not desc_match:
#                         continue

#                     desc = desc_match.group(1).strip()
#                     numbers = re.findall(r'([\d,]+\.?\d*)', line)

#                     if numbers:
#                         txn_data = {
#                             'entity_name': entity,
#                             'amc_name': amc,
#                             'folio_number': folio,
#                             'isin': isin,
#                             'scheme_name': scheme,
#                             'transaction_date': parse_date(txn_date),
#                             'transaction_description': desc,
#                             'value': safe_decimal(numbers[0]) if len(numbers) > 0 else None,
#                             'units': safe_decimal(numbers[1]) if len(numbers) > 1 else None,
#                             'nav': safe_decimal(numbers[2]) if len(numbers) > 2 else None,
#                             'unit_balance': safe_decimal(numbers[3]) if len(numbers) > 3 else None,
#                         }

#                         if desc.lower() == "purchase":
#                             last_purchase = txn_data
#                         elif "stamp" in desc.lower() and last_purchase:
#                             last_purchase['stamp_duty'] = safe_decimal(numbers[0])
#                             CAMSTransaction.objects.create(**last_purchase)
#                             transaction_count += 1
#                             last_purchase = None
#                         else:
#                             CAMSTransaction.objects.create(**txn_data)
#                             transaction_count += 1

#             except Exception:
#                 continue

#     return {
#         "transactions": transaction_count,
#         "summaries": summary_count,
#         "files_processed": len(txt_files)
#     }


COLUMN_MAP = {
    'Folio': 'folio_no',
    'Investor Name': 'entity_name',
    'Scheme': 'scheme_name',
    'Cost Value(Rs.)': 'cost_value',
    'Unit Balance': 'unit_balance',
    'NAV Date': 'nav_date',
    'Current Value(Rs.)': 'market_value'
}


@transaction.atomic
def import_cams_portfolio_with_pandas(folder='cams_gmail_data', user=None):
    """
    Reads all Excel files in folder using pandas, maps columns, and updates/inserts into CamsPortfolio model.
    """
    for filename in os.listdir(folder):
        if not filename.lower().endswith(('.xlsx', '.xls')):
            continue
        filepath = os.path.join(folder, filename)
        df = pd.read_excel(filepath, skiprows=1)

        # Select and rename columns
        df = df[list(COLUMN_MAP.keys())]
        df.rename(columns=COLUMN_MAP, inplace=True)

        # Convert NAV Date to datetime
        df['nav_date'] = pd.to_datetime(df['nav_date'], errors='coerce')

        # Extract month and year
        df['month'] = df['nav_date'].dt.month
        df['year'] = df['nav_date'].dt.year

        for _, row in df.iterrows():
            row_data = row.to_dict()
            if user:
                row_data['updated_by'] = user

            # Use folio_no + scheme_name + nav_date as unique keys for update_or_create
            obj, created = CamsPortfolio.objects.update_or_create(
                folio_no=row_data['folio_no'],
                scheme_name=row_data['scheme_name'],
                nav_date=row_data['nav_date'],
                defaults=row_data
            )



