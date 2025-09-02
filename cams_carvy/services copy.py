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
    Returns summary dict with counts.
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

    bulk_txns = []
    bulk_summaries = []

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
                    txn_match = re.match(
                        r'^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)', line)
                    if txn_match:

                        txn_date = txn_match.group(1)
                        txn_date = datetime.strptime(
                            txn_date, "%d-%b-%Y").date()

                        # print(txn_date,"jjjjj",txn_match.group(1))
                        desc_pattern = r"\d{2}-[A-Za-z]{3}-\d{4}\s+(.*?)(?=\s+\(|\s+\d{1,3}(?:,\d{3})*\.\d{2})"
                        desc_match = re.search(desc_pattern, line)
                        desc = desc_match.group(
                            1).strip() if desc_match else None

                        val_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,4}|\d+\.\d{2,4}"
                        values = re.findall(val_pattern, line)

                        txn_value = Decimal(values[0].replace(
                            ",", "")) if len(values) > 0 else None
                        txn_units = Decimal(values[1].replace(
                            ",", "")) if len(values) > 1 else None
                        txn_nav = Decimal(values[2].replace(
                            ",", "")) if len(values) > 2 else None
                        txn_unitbal = Decimal(values[3].replace(
                            ",", "")) if len(values) > 3 else None

                        if desc:
                            if "purchase" in desc.lower():
                                last_purchase = dict(
                                    entity_name=curr_entity,
                                    amc_name=curr_amc,
                                    folio_number=curr_folio,
                                    isin=curr_isin,
                                    scheme_name=curr_scheme,
                                    transaction_date=txn_date,
                                    transaction_description=desc,
                                    value=txn_value,
                                    stamp_duty=None,
                                    units=txn_units,
                                    nav=txn_nav,
                                    unit_balance=txn_unitbal,
                                )
                            elif "stamp" in desc.lower():
                                if last_purchase:
                                    last_purchase["stamp_duty"] = txn_value
                                    bulk_txns.append(
                                        CAMSTransaction(**last_purchase))
                                    last_purchase = {}
                            else:
                                bulk_txns.append(
                                    CAMSTransaction(
                                        entity_name=curr_entity,
                                        amc_name=curr_amc,
                                        folio_number=curr_folio,
                                        isin=curr_isin,
                                        scheme_name=curr_scheme,
                                        transaction_date=txn_date,
                                        transaction_description=desc,
                                        value=txn_value,
                                        stamp_duty=0.00,
                                        units=txn_units,
                                        nav=txn_nav,
                                        unit_balance=txn_unitbal,
                                    )
                                )

                # --- Summary Processing ---
                if curr_entity and curr_folio and curr_isin and curr_scheme:
                    if "closing unit balance" in line.lower():
                        print(line)
                        nav_date_match = re.search(r'NAV on (\d{1,2}-[A-Za-z]{3}-\d{4})', line)
                        if nav_date_match:
                            nav_date = nav_date_match.group(1)
                        else: 
                            pass
                        parsed_date = datetime.strptime(nav_date, "%d-%b-%Y").date()
                        summary = parse_summary_line(line)
                        print(line,summary.get(
                                    "Closing Unit Balance"),summary.get(
                                    "Total Cost Value"),summary.get(
                                    "NAV"),summary.get(
                                    "Market Value"))
                        bulk_summaries.append(
                            # CAMSSummary(
                            #     entity_name=curr_entity,
                            #     amc_name=curr_amc,
                            #     folio_number=curr_folio,
                            #     isin=curr_isin,
                            #     scheme_name=curr_scheme,
                            #     closing_unit_balance=summary.get("Closing Unit Balance"),
                            #     nav=summary.get("NAV"),
                            #     total_cost_value=summary.get("Total Cost Value"),
                            #     market_value=summary.get("Market Value"),
                            # )
                            CAMSSummary(
                                entity_name=curr_entity,
                                amc_name=curr_amc,
                                folio_number=curr_folio,
                                isin=curr_isin,
                                scheme_name=curr_scheme,
                                closing_unit_balance=summary.get(
                                    "Closing Unit Balance") or 0.00,
                                nav=summary.get("NAV") or 0.00,
                                total_cost_value=summary.get(
                                    "Total Cost Value") or 0.00,
                                market_value=summary.get(
                                    "Market Value") or 0.00,
                                nav_date=parsed_date
                            )

                        )

    # ✅ DB Insert
    tx_count = sm_count = 0
    if bulk_txns:
        CAMSTransaction.objects.bulk_create(bulk_txns, ignore_conflicts=True)
        tx_count = len(bulk_txns)
    if bulk_summaries:
        CAMSSummary.objects.bulk_create(bulk_summaries, ignore_conflicts=True)
        sm_count = len(bulk_summaries)

    return {
        "transactions_inserted": tx_count,
        "summaries_inserted": sm_count,
        "message": "✅ CAS parsing completed"
    }


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


load_dotenv()

# Configuration
SUBJECT_LINE = "CAMS Mailback"
CAMS_FOLDER = "cams_gmail_data"
PROCESSED_FILE = "processed_emails.txt"
PDF_DATA_FOLDER = "pdf_extracted_data"

# HARDCODED PASSWORDS ONLY


def get_hardcoded_passwords():
    """Get list of passwords, avoiding duplicates"""
    passwords = []
    # file_password = os.getenv('FILE_PASSWORD', '').strip()
    file_password = 'Zomato@123'
    if file_password:
        passwords.append(file_password)
    if '' not in passwords:  # Add empty password if not already present
        passwords.append('')
    return passwords


def validate_imap_environment():
    """Validate required environment variables exist for IMAP"""
    required_vars = ['EMAIL', 'App_Password']  # Fixed to match actual usage
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        return False
    return True


def connect_to_imap():
    """Connect to IMAP server"""
    if not validate_imap_environment():
        return None

    try:
        # Use env var with fallback
        imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        email_address = os.getenv('EMAIL')
        email_password = os.getenv("App_Password")

        if not email_address or not email_password:
            print("Error: Email credentials not found in environment variables")
            return None

        # Connect to server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, email_password)
        print("✓ Connected to IMAP server successfully")
        return mail
    except Exception as e:
        print(f"Error connecting to IMAP server: {e}")
        return None


def decode_mime_words(text):
    """Decode MIME encoded words"""
    try:
        decoded_fragments = decode_header(text)
        decoded_text = ''
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    decoded_text += fragment.decode(encoding)
                else:
                    decoded_text += fragment.decode('utf-8', errors='ignore')
            else:
                decoded_text += fragment
        return decoded_text
    except Exception as e:
        print(f"Error decoding MIME words: {e}")
        return str(text)


def load_processed_emails():
    """Load list of already processed email IDs"""
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(line.strip() for line in f)
    except Exception as e:
        print(f"Error loading processed emails: {e}")
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
    passwords = get_hardcoded_passwords()

    for password in passwords:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if password:
                    zip_ref.extractall(
                        CAMS_FOLDER, pwd=password.encode('utf-8'))
                    print(f"✓ Extracted {zip_filename} with password")
                else:
                    zip_ref.extractall(CAMS_FOLDER)
                    print(f"✓ Extracted {zip_filename} (no password)")

                for file in zip_ref.namelist():
                    print(f"  - {file}")
                return True
        except Exception as e:
            continue

    print(f"✗ Could not extract {zip_filename} with available passwords")
    return False


def extract_current_valuation(zip_path, zip_filename):
    """Extract only 'current valuation' file from zip"""
    passwords = get_hardcoded_passwords()

    for password in passwords:
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
                        zip_ref.extract(
                            current_val_file, CAMS_FOLDER, pwd=password.encode('utf-8'))
                    else:
                        zip_ref.extract(current_val_file, CAMS_FOLDER)
                    print(f"✓ Extracted: {current_val_file}")

                    # Move to main folder if in subfolder
                    extracted_path = os.path.join(
                        CAMS_FOLDER, current_val_file)
                    if os.path.dirname(current_val_file):
                        new_path = os.path.join(
                            CAMS_FOLDER, os.path.basename(current_val_file))
                        try:
                            shutil.move(extracted_path, new_path)
                            # Clean up empty directories
                            parent_dir = os.path.dirname(extracted_path)
                            if parent_dir != CAMS_FOLDER and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                        except Exception as e:
                            print(f"Warning: Could not move file: {e}")
                else:
                    # Extract all if current valuation not found
                    if password:
                        zip_ref.extractall(
                            CAMS_FOLDER, pwd=password.encode('utf-8'))
                    else:
                        zip_ref.extractall(CAMS_FOLDER)
                    print(f"✓ Extracted all files from {zip_filename}")
                return True
        except Exception as e:
            continue

    print(f"✗ Could not extract {zip_filename} with available passwords")
    return False


def remove_pdf_password(pdf_path):
    """Remove password from PDF file"""
    try:
        reader = PdfReader(pdf_path)

        if not reader.is_encrypted:
            print(f"✓ PDF {os.path.basename(pdf_path)} not encrypted")
            return pdf_path

        # Try to decrypt
        passwords = get_hardcoded_passwords()
        for password in passwords:
            try:
                if reader.decrypt(password):
                    base_name = os.path.splitext(pdf_path)[0]
                    output_path = f"{base_name}_unlocked.pdf"

                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)

                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)

                    print(
                        f"✓ Created unlocked PDF: {os.path.basename(output_path)}")

                    # Safely remove encrypted version
                    try:
                        os.remove(pdf_path)
                    except Exception as e:
                        print(f"Warning: Could not remove encrypted PDF: {e}")

                    return output_path
            except Exception as e:
                continue

        print(
            f"✗ Could not unlock PDF {os.path.basename(pdf_path)} - deleting")
        try:
            os.remove(pdf_path)
        except Exception as e:
            print(f"Warning: Could not delete encrypted PDF: {e}")
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
        output_file = os.path.join(
            PDF_DATA_FOLDER, f"{base_name}_extracted.txt")

        extracted_data = []

        with pdfplumber.open(pdf_path) as pdf:
            print(
                f"Processing PDF: {os.path.basename(pdf_path)} ({len(pdf.pages)} pages)")

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    extracted_data.append(f"=== PAGE {page_num} ===\n")
                    extracted_data.append(text)
                    extracted_data.append("\n" + "="*50 + "\n")

                tables = page.extract_tables()
                if tables:
                    extracted_data.append(
                        f"\n=== TABLES FROM PAGE {page_num} ===\n")
                    for table_num, table in enumerate(tables, 1):
                        extracted_data.append(f"\nTable {table_num}:\n")
                        for row in table:
                            if row:
                                row_data = [
                                    str(cell) if cell is not None else "" for cell in row]
                                extracted_data.append(
                                    " | ".join(row_data) + "\n")

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
        print(f"CAMS folder '{CAMS_FOLDER}' does not exist")
        return

    pdf_files = [f for f in os.listdir(
        CAMS_FOLDER) if f.lower().endswith('.pdf')]

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


def download_cams_zip(url):
    """Download CAMS zip file"""
    try:
        print(f"Downloading CAMS file from: {url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        filename = url.split('fname=')[1].split(
            '&')[0] if 'fname=' in url else f"cams_{abs(hash(url)) % 10000}.zip"
        if not filename.endswith('.zip'):
            filename += '.zip'

        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        filepath = os.path.join(CAMS_FOLDER, filename)

        # Ensure directory exists
        os.makedirs(CAMS_FOLDER, exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"Saved CAMS zip: {filename}")
        extract_current_valuation(filepath, filename)

        # Delete zip file
        try:
            os.remove(filepath)
            print(f"Deleted zip file: {filename}")
        except Exception as e:
            print(f"Warning: Could not delete zip file: {e}")

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


def process_email_attachments(msg):
    """Process email attachments"""
    try:
        os.makedirs(CAMS_FOLDER, exist_ok=True)

        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    filename = decode_mime_words(filename)
                    filename = "".join(
                        c for c in filename if c.isalnum() or c in "._-")

                    if filename.lower().endswith(('.zip', '.pdf')):
                        filepath = os.path.join(CAMS_FOLDER, filename)

                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))

                        print(f"Downloaded attachment: {filename}")

                        if filename.lower().endswith('.zip'):
                            extract_zip(filepath, filename)
    except Exception as e:
        print(f"Error processing attachments: {e}")


def get_email_body(msg):
    """Extract email body text"""
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(
                        charset, errors='ignore')
                    break
                elif part.get_content_type() == "text/html" and not body:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(
                        charset, errors='ignore')
        else:
            charset = msg.get_content_charset() or 'utf-8'
            body = msg.get_payload(decode=True).decode(
                charset, errors='ignore')
    except Exception as e:
        print(f"Error extracting email body: {e}")

    return body


def process_cams_emails(subject_filter=SUBJECT_LINE, mailbox='INBOX', limit=None):
    """
    Main function to process CAMS emails using IMAP

    Args:
        subject_filter (str): Subject line to search for
        mailbox (str): Mailbox to search in (default: 'INBOX')
        limit (int): Maximum number of emails to process (None for all)

    Returns:
        bool: True if successful, False otherwise
    """
    print("Starting IMAP CAMS Email Processor...")

    # Connect to IMAP server
    mail = connect_to_imap()
    if not mail:
        return False

    try:
        os.makedirs(CAMS_FOLDER, exist_ok=True)
        processed_emails = load_processed_emails()

        # Select mailbox
        mail.select(mailbox)

        # Search for emails with specific subject
        search_criteria = f'(SUBJECT "{subject_filter}")'
        status, messages = mail.search(None, search_criteria)

        if status != 'OK':
            print(f"Error searching for emails: {status}")
            return False

        email_ids = messages[0].split()
        if not email_ids:
            print(f'No emails found with subject: {subject_filter}')
            return True

        # Filter out already processed emails
        new_email_ids = [eid.decode()
                         for eid in email_ids if eid.decode() not in processed_emails]

        if not new_email_ids:
            print('No new emails to process')
            return True

        # Apply limit if specified
        if limit:
            new_email_ids = new_email_ids[-limit:]  # Get most recent emails

        print(f'Found {len(new_email_ids)} new emails to process')

        for email_id in new_email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    print(f"Error fetching email {email_id}")
                    continue

                # Parse email
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # Get subject
                subject = decode_mime_words(
                    email_message.get('Subject', 'No Subject'))
                print(f"Processing: {subject}")

                # Extract and process email body for CAMS links
                body = get_email_body(email_message)
                download_zip_from_body(body)

                # Process attachments
                process_email_attachments(email_message)

                # Mark as processed
                save_processed_email(email_id)

            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
                continue

        print(f"All attachments saved to '{CAMS_FOLDER}' folder")

        print("\nProcessing PDF files...")
        process_pdf_files()

        print("\nEmail processing completed successfully!")
        return True

    except Exception as e:
        print(f"Error during email processing: {e}")
        return False

    finally:
        try:
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"Error closing IMAP connection: {e}")

# Example usage
# if __name__ == "__main__":
#     process_cams_emails()
