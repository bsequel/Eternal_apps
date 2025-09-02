import os
import re
import email
import imaplib
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter
from .utils import extract_ack_no
from .models import CyberCellReport  # Your model storing ack_no
# from .custom_exception import DuplicateAckNumberError

# class DuplicateAckNumberError(Exception):
#     """Raised when an email contains an acknowledge number that already exists in the DB."""
#     pass




load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("App_Password")
PDF_PASSWORD = os.getenv("PDF_PASSWORD")

GMAIL_HOST = 'imap.gmail.com'
GMAIL_PORT = 993
SUBJECT_KEYWORD = "NCRP MHA Acknowledgement No"

SOURCE_DIR = "EMAIL_PDFS"
DECRYPTED_DIR = "DECRYPTED_PDFS"

os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)



def remove_pdf_password(input_path, output_path, password):
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
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


def fetch_and_decrypt_pdfs():
    decrypted_info = []

    mail = imaplib.IMAP4_SSL(GMAIL_HOST, GMAIL_PORT)
    mail.login(EMAIL, APP_PASSWORD)
    mail.select('inbox')

    _, messages = mail.search(None, 'UNSEEN')
    email_ids = messages[0].split()

    for email_id in email_ids:
        _, msg_data = mail.fetch(email_id, '(BODY.PEEK[])')
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg.get("Subject", "")

        if SUBJECT_KEYWORD.lower() not in subject.lower():
            continue

        ack_no = extract_ack_no(subject)
        if not ack_no:
            print("❌ Acknowledgement number missing in subject.")
            continue
        if CyberCellReport.objects.filter(reference_number=ack_no).exists():
            print("❌ Report already exists in database.")
            # raise DuplicateAckNumberError(f"Skipping email {email_id} — duplicate ack_no {ack_no} found in DB."
            # )
            continue
            

        decrypted_path = None
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                ext = os.path.splitext(part.get_filename())[1] or ".pdf"
                raw_path = os.path.abspath(
                    os.path.join(SOURCE_DIR, f"{ack_no}{ext}"))
                decrypted_path_candidate = os.path.abspath(
                    os.path.join(DECRYPTED_DIR, f"{ack_no}{ext}"))

                with open(raw_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                print(f"📥 Downloaded: {raw_path}")

                if remove_pdf_password(raw_path, decrypted_path_candidate, PDF_PASSWORD):
                    decrypted_path = decrypted_path_candidate
                    break

        if decrypted_path:
            decrypted_info.append((email_id, decrypted_path))
            # decrypted_info.append(decrypted_path)

    mail.logout()

    return decrypted_info
