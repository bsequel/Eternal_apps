from cyber_app.utils import extract_month_from_string, calculate_ageing_days1
from cyber_app.pdf_parser import extract_structured_data_from_pdf
from cyber_app.models import CyberCellReport
from django.contrib.auth.models import User
import json
import os
from django.core.files import File

# def extract_and_insert_data_from_pdf(output_pdf: str, updated_by_username: str = None):
#     try:
#         print(f"Processing PDF: {output_pdf}, updated_by_username: {updated_by_username}")

#         # Extract structured data JSON path from PDF
#         json_path = extract_structured_data_from_pdf(output_pdf)
#         print(f"JSON saved at: {json_path}")

#         # Load extracted JSON data
#         with open(json_path, "r", encoding="utf-8") as file:
#             records = json.load(file)

#         line_items = records.get('LineItems', [])
#         month_name, _ = extract_month_from_string(records.get('MailDate', ''))

#         # Fetch user if username provided
#         user = None
#         if updated_by_username:
#             try:
#                 user = User.objects.get(username=updated_by_username)
#             except User.DoesNotExist:
#                 print(f"User '{updated_by_username}' not found. Proceeding without updated_by.")

#         # Open PDF file ONCE and reuse django_file for each record save
#         with open(output_pdf, 'rb') as f_pdf:
#             django_file = File(f_pdf)

#             for item in line_items:
#                 print("Inserting:", item)
#                 age_days = calculate_ageing_days1(item.get("ComplaintDate", ""))

#                 # Create report instance WITHOUT saving yet
#                 report = CyberCellReport(
#                     complaint_date=item.get("ComplaintDate", ""),
#                     mail_date=records.get("MailDate", ""),
#                     mail_month=month_name,
#                     amount=item.get("Amount", ""),
#                     reference_number=records.get("RefNo", ""),
#                     police_station_address=records.get("Police_Station_Address", ""),
#                     account_number=item.get("Account_No", ""),
#                     name=records.get("Name", ""),
#                     mobile_number=records.get("Mobile", [""])[0],
#                     email_id=records.get("Email", ""),
#                     ageing_days=age_days,
#                     debit_from_bank='no',  # default
#                     region=item.get("Region", ""),
#                     utr_number=item.get("UTR_No", ""),
#                     utr_amount=item.get("UTR_Amount", ""),
#                     transaction_datetime=item.get("Transaction_Date", ""),
#                     total_fraudulent_amount=records.get("Total_Fraudulent_Amount", ""),
#                     updated_by=user,  # optional
#                 )

#                 # Before saving, reset django_file's pointer to the start
#                 django_file.seek(0)
#                 # Save pdf file to model field and save instance
#                 report.pdf_file.save(os.path.basename(output_pdf), django_file, save=True)

#         print("✅ All records inserted successfully.")

#     except Exception as e:
#         print("Error:", e)
# def extract_and_insert_data_from_pdf(output_pdf: str, updated_by_username: str = None):
#     try:
#         print(f"Processing PDF: {output_pdf}, updated_by_username: {updated_by_username}")

#         # Extract structured data JSON path from PDF
#         json_path = extract_structured_data_from_pdf(output_pdf)
#         print(f"JSON saved at: {json_path}")

#         # Load extracted JSON data
#         with open(json_path, "r", encoding="utf-8") as file:
#             records = json.load(file)

#         line_items = records.get('LineItems', [])
#         month_name, _ = extract_month_from_string(records.get('MailDate', ''))

#         # Fetch user if username provided
#         user = None
#         if updated_by_username:
#             try:
#                 user = User.objects.get(username=updated_by_username)
#             except User.DoesNotExist:
#                 print(f"User '{updated_by_username}' not found. Proceeding without updated_by.")

#         # Open PDF file once and prepare File instance
#         with open(output_pdf, 'rb') as f_pdf:
#             django_file = File(f_pdf)
            
#             # Save the PDF file only once; create a placeholder to reuse the same file path
#             # We create a dummy instance just to store the PDF file once
#             dummy_report = CyberCellReport()
#             dummy_report.pdf_file.save(os.path.basename(output_pdf), django_file, save=False)
#             # Save dummy_report to get it committed and pdf_file path stored
#             dummy_report.save()
#             saved_pdf_file = dummy_report.pdf_file.name  # Store the file's path string

#             # Now create actual reports for each entry, linking the same pdf_file field
#             for item in line_items:
#                 print("Inserting:", item)
#                 age_days = calculate_ageing_days1(item.get("ComplaintDate", ""))

#                 report = CyberCellReport(
#                     complaint_date=item.get("ComplaintDate", ""),
#                     mail_date=records.get("MailDate", ""),
#                     mail_month=month_name,
#                     amount=item.get("Amount", ""),
#                     reference_number=records.get("RefNo", ""),
#                     police_station_address=records.get("Police_Station_Address", ""),
#                     account_number=item.get("Account_No", ""),
#                     name=records.get("Name", ""),
#                     mobile_number=records.get("Mobile", [""])[0],
#                     email_id=records.get("Email", ""),
#                     ageing_days=age_days,
#                     debit_from_bank='no',  # default
#                     region=item.get("Region", ""),
#                     utr_number=item.get("UTR_No", ""),
#                     utr_amount=item.get("UTR_Amount", ""),
#                     transaction_datetime=item.get("Transaction_Date", ""),
#                     total_fraudulent_amount=records.get("Total_Fraudulent_Amount", ""),
#                     updated_by=user,  # optional
#                 )
#                 # **Assign the same saved PDF file path to all entries**
#                 report.pdf_file.name = saved_pdf_file

#                 # Save the report entry
#                 report.save()

#             print("✅ All records inserted successfully.")

#     except Exception as e:
#         print("Error:", e)
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
            age_days = calculate_ageing_days1(item.get("ComplaintDate", ""))
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
                ageing_days=age_days,
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
