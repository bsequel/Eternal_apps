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
from django.db import transaction
import pandas as pd
# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.conf import settings
from . models import *

from datetime import datetime
from django.db import IntegrityError
import pytz
# Load environment
# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)
load_dotenv()

# Base data folder
BASE_FOLDER = "cams_data"
CAMS_FOLDER = os.path.join(BASE_FOLDER, "gmail_files")
PDF_DATA_FOLDER = os.path.join(BASE_FOLDER, "pdf_extracted")

# Configuration
SUBJECT_KEYWORD = "CAMS Mailback"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# File paths

TOKEN_FILE = settings.GOOGLE_TOKEN_PATH
CREDENTIALS_FILE = settings.GOOGLE_CREDENTIALS_PATH

# Fixed ZIP password
ZIP_PASSWORD = "Zomato@123"
# ======================================     gmail part   ===============================================

def ensure_directories():
    os.makedirs(BASE_FOLDER, exist_ok=True)
    os.makedirs(CAMS_FOLDER, exist_ok=True)
    os.makedirs(PDF_DATA_FOLDER, exist_ok=True)


def save_tokens(creds: Credentials):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


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


def mark_email_as_read(service, message_id):
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        print(f"✓ Marked message {message_id} as read")
    except Exception as e:
        print(f"❌ Failed to mark {message_id} as read: {e}")


def extract_current_valuation(zip_path, zip_filename):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            test_file = zip_ref.namelist()[0]
            zip_ref.read(test_file, pwd=ZIP_PASSWORD.encode('utf-8'))

            current_val_file = None
            for file in zip_ref.namelist():
                if 'current' in file.lower() and 'valuation' in file.lower():
                    current_val_file = file
                    break

            if current_val_file:
                zip_ref.extract(current_val_file, CAMS_FOLDER, pwd=ZIP_PASSWORD.encode('utf-8'))
                print(f"✓ Extracted: {current_val_file}")

                extracted_path = os.path.join(CAMS_FOLDER, current_val_file)
                if os.path.dirname(current_val_file):
                    new_path = os.path.join(CAMS_FOLDER, os.path.basename(current_val_file))
                    os.rename(extracted_path, new_path)
                    try:
                        os.rmdir(os.path.dirname(extracted_path))
                    except:
                        pass
                else:
                    new_path = extracted_path

                os.remove(zip_path)
                return new_path
            else:
                print(f"✗ No 'current valuation' file found in {zip_filename}")
                os.remove(zip_path)
                return None
    except Exception as e:
        print(f"✗ Could not extract {zip_filename}: {e}")
        os.remove(zip_path)
        return None


def remove_pdf_password(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        if not reader.is_encrypted:
            print(f"✓ PDF {os.path.basename(pdf_path)} not encrypted")
            return pdf_path
        if reader.decrypt(ZIP_PASSWORD):
            base_name = os.path.splitext(pdf_path)[0]
            output_path = f"{base_name}_unlocked.pdf"
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            print(f"✓ Created unlocked PDF: {os.path.basename(output_path)}")
            os.remove(pdf_path)
            return output_path
        else:
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
    try:
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


def extract_message_body_from_payload(payload):
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
    try:
        print(f"Downloading CAMS file from: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
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
        return extract_current_valuation(filepath, filename)
    except Exception as e:
        print(f"Error downloading CAMS file: {e}")
        return None


def download_zip_from_body(body):
    if not body:
        return
    cams_pattern = r'https://[\w.-]+/dnldresult\.asp\?fname=[^"\s<>]+'
    cams_urls = re.findall(cams_pattern, body, re.IGNORECASE)
    print(f"Found {len(cams_urls)} CAMS download links")
    for url in cams_urls:
        download_cams_zip(url)


def download_attachments_from_message(service, msg_id, payload):
    if 'parts' not in payload:
        return
    for part in payload['parts']:
        if part.get("filename") and part.get("body", {}).get("attachmentId"):
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_id, id=att_id
            ).execute()
            file_data = base64.urlsafe_b64decode(att["data"].encode("UTF-8"))

            filepath = os.path.join(CAMS_FOLDER, part['filename'])
            with open(filepath, "wb") as f:
                f.write(file_data)
            print(f"✓ Saved attachment: {filepath}")

            if filepath.lower().endswith(".zip"):
                extract_current_valuation(filepath, part['filename'])


def download_attachments_with_google_api(subject_filter):
    ensure_directories()
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
        print(f'Found {len(messages)} messages')
        for message in messages:
            try:
                msg_data = service.users().messages().get(userId="me", id=message["id"]).execute()
                headers = msg_data.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                print(f"Processing: {subject}")

                payload = msg_data.get('payload', {})

                download_attachments_from_message(service, message["id"], payload)

                body = extract_message_body_from_payload(payload)
                download_zip_from_body(body)

                mark_email_as_read(service, message['id'])
            except Exception as e:
                print(f"❌ Error processing message {message.get('id', 'unknown')}: {e}")
                continue
    except Exception as error:
        print(f'❌ Gmail API error: {error}')
# ======================================     gmail part   ===============================================


# ======================================     extraction part   ===============================================
import os
from pathlib import Path
import re
import json

cams_transactions = []
cams_summary = []

# ---------- Utility for parsing summary ----------
def parse_summary_line(line: str) -> dict:
    """
    Extracts all label:value numeric pairs from a single summary line.
    Handles optional 'INR' / '₹' and thousands separators.
    Ensures NAV key is always 'NAV' (removes trailing date).
    """
    pairs = re.findall(r'([^:|]+):\s*(?:INR|₹)?\s*([-]?\d[\d,]*(?:\.\d+)?)', line)
    result = {}
    for key, val in pairs:
        key = key.strip()
        # normalize key (remove trailing date e.g. NAV on 20-Aug-2025 -> NAV)
        key = re.sub(r"\s+on\s+\d{1,2}-[A-Za-z]{3}-\d{4}", "", key, flags=re.IGNORECASE).strip()
        num = float(val.replace(",", "").strip())
        result[key] = num
    return result


# ---------- Reader for CAMS TXT ----------
def read_cams_txt_files(folder="pdf_extracted_data"):
    """Read only .txt files starting with CAS in the given folder"""
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"❌ Folder '{folder}' not found.")
        return

    txt_files = [f for f in folder_path.glob("CAS*.txt")]

    if not txt_files:
        print("⚠️ No CAMS text files found.")
        return

    limited_variants = [
        "Ltd", "Ltd.", "LTD", "LTD.", "Limited", "LIMITED", "ltd", "ltd.",
        "limited", "Limited Company", "LIMITED COMPANY", "Ltd Company", "LTD COMPANY"
    ]

    for txt_file in txt_files:
        print(f"\n📄 Reading file: {txt_file.name}")
        print("="*50)

        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.readlines()

            curr_amc = None
            curr_entity = None
            curr_folio = None
            curr_isin = None
            curr_scheme = None
            last_purchase = {}

            for idx, line in enumerate(content, 1):
                try:
                    parts = line.split()
                    # AMC name
                    if line.strip().endswith("Mutual Fund"):
                        curr_amc = line.strip()
                        # reset on new fund
                        curr_entity = None
                        curr_folio = None
                        curr_isin = None
                        curr_scheme = None
                        continue

                    if curr_amc:
                        # Entity name
                        if parts and parts[-1] in limited_variants:
                            curr_entity = line.strip()

                        # Folio number
                        folio_match = re.search(r'Folio No:\s*([A-Za-z0-9/]+)', line)
                        if folio_match:
                            curr_folio = folio_match.group(1).strip()

                        # ISIN + Scheme
                        match = re.match(r"^(.*?)\s*-\s*ISIN:\s*([A-Z0-9]+)(?:\(Advisor:\s*([A-Z0-9]+)\))?", line)
                        if match:
                            scheme, isin, _ = match.groups()
                            curr_isin = isin.strip()
                            curr_scheme = scheme.strip()

                        # ---------------- Transactions ----------------
                        if curr_entity and curr_folio and curr_isin and curr_scheme:
                            txn_match = re.match(r'^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)', line)
                            if txn_match:
                                txn_date = txn_match.group(1)

                                desc_pattern = r"\d{2}-[A-Za-z]{3}-\d{4}\s+(.*?)(?=\s+\(|\s+\d{1,3}(?:,\d{3})*\.\d{2})"
                                desc_match = re.search(desc_pattern, line)
                                desc = desc_match.group(1).strip() if desc_match else None

                                val_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,4}|\d+\.\d{2,4}"
                                values = re.findall(val_pattern, line)

                                txn_value = values[0] if len(values) > 0 else None
                                txn_units = values[1] if len(values) > 1 else None
                                txn_nav = values[2] if len(values) > 2 else None
                                txn_unitbal = values[3] if len(values) > 3 else None

                                if desc:
                                    if "purchase" in desc.lower():
                                        last_purchase = {
                                            "Entity Name": curr_entity,
                                            "AMC Name": curr_amc,
                                            "Folio Number": curr_folio,
                                            "ISIN and Scheme Name": f"{curr_isin} {curr_scheme}",
                                            "Transaction Date": txn_date,
                                            "Transaction Description": desc,
                                            "Value (Neg or Pos)": txn_value,
                                            "Stamp Duty": None,
                                            "Units": txn_units,
                                            "NAV": txn_nav,
                                            "Unit Balance": txn_unitbal
                                        }
                                    elif "stamp" in desc.lower():
                                        if last_purchase:
                                            last_purchase["Stamp Duty"] = txn_value
                                            cams_transactions.append(last_purchase)
                                            last_purchase = {}
                                    else:
                                        cams_transactions.append({
                                            "Entity Name": curr_entity,
                                            "AMC Name": curr_amc,
                                            "Folio Number": curr_folio,
                                            "ISIN and Scheme Name": f"{curr_isin} {curr_scheme}",
                                            "Transaction Date": txn_date,
                                            "Transaction Description": desc,
                                            "Value (Neg or Pos)": txn_value,
                                            "Stamp Duty": None,
                                            "Units": txn_units,
                                            "NAV": txn_nav,
                                            "Unit Balance": txn_unitbal
                                        })

                        # ---------------- Summary ----------------
                        if curr_entity and curr_folio and curr_isin and curr_scheme:
                            if "closing unit balance" in line.lower():
                                summary = parse_summary_line(line)
                                record = {
                                    "Entity Name": curr_entity,
                                    "AMC Name": curr_amc,
                                    "Folio Number": curr_folio,
                                    "ISIN and Scheme Name": f"{curr_isin} {curr_scheme}",
                                    "Closing Unit Balance": summary.get("Closing Unit Balance"),
                                    "NAV": summary.get("NAV"),
                                    "Total Cost Value": summary.get("Total Cost Value"),
                                    "Market Value": summary.get("Market Value"),
                                }
                                cams_summary.append(record)

                except Exception:
                    continue

        except Exception as e:
            print(f"❌ Error reading {txt_file.name}: {e}")


# ---------- Save JSON ----------
def save_data_to_json(data, filename):
    """Save parsed data to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save {filename}: {e}")
# ======================================     extraction part   ===============================================



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
def import_cams_portfolio_with_pandas(folder='gmail_files', user=None):
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

def main():
    print("Starting Gmail CAMS Processor with Google API...")
    try:
        # -------------  mail part  ---------------------------------
        download_attachments_with_google_api(SUBJECT_KEYWORD)
        print(f"All attachments saved to '{CAMS_FOLDER}' folder")
        print("\nProcessing PDF files...")
        process_pdf_files()
        print("\nProcessing completed!")
        # --------------- mail part   ---------------------------------

        # --------------- extraction part   ---------------------------

        read_cams_txt_files("cams_data/pdf_extracted")

        # Save transactions separately
        save_data_to_json(cams_transactions, "cams_data/cams_transaction.json")
        print(f"📊 Total transactions parsed: {len(cams_transactions)}")

        # Save scheme summary separately
        save_data_to_json(cams_summary, "cams_data/cams_summary.json")
        print(f"📊 Total summaries parsed: {len(cams_summary)}")


        # --------------- extraction part   ---------------------------

        # --------- cams portfolio insert------------------------------
        import_cams_portfolio_with_pandas(CAMS_FOLDER)
        # --------- cams transaction insert----------------------------
        # --------- cams summary insert--------------------------------
        process_cams_files(PDF_DATA_FOLDER)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# if __name__ == '__main__':
#     count = check_unread_mails()
#     if count == 0:
#         print("📭 No unread mails")
#     else:
#         print(f"📧 You have {count} unread mails")
#         main()
