import imaplib
import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .email_handler import fetch_and_decrypt_pdfs
from .db_operations import extract_and_insert_data_from_pdf
from .models import CyberCellReport
import imaplib
# from .utils import fetch_and_decrypt_pdfs, extract_and_insert_data_from_pdf  # Adjust based on your structure
from .email_handler import fetch_and_decrypt_pdfs
from .db_operations import extract_and_insert_data_from_pdf
from .email_utils import notify_admin
from django_filters import rest_framework as filters

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
import django_filters

# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status
from .models import CyberCellReport

from datetime import datetime
from .date_parser import parse_date
from django.utils import timezone
from django.contrib.auth.decorators import login_required

load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("App_Password")
GMAIL_HOST = 'imap.gmail.com'
GMAIL_PORT = 993


def home(request):
    return render(request, 'home.html')


# @login_required
# def run_pdf_etl(request):
#     try:
#         decrypted_info = fetch_and_decrypt_pdfs()
#         subject = "[ETL Report] No New PDFs to Process"
#         message = (
#             "Dear Team,\n\n"
#             "This is to inform you that the scheduled ETL job has completed successfully.\n\n"
#             "However, no new unread emails containing valid PDF attachments were found for processing during this run.\n\n"
#             "Summary:\n"
#             "- PDFs Processed: 0\n"
#             "- Successfully Processed: 0\n\n"
#             "No action is required at this time.\n\n"
#             "Best regards,\n"
#             "ETL Automation System"
#         )

#         # notify_admin(subject,message)
#         if not decrypted_info:
#             notify_admin(subject, message)
#             return JsonResponse({
#                 "message": "No unread emails with valid PDFs found.",
#                 "pdfs_processed": 0,
#                 "successfully_processed": 0
#             })

#         success_count = 0

#         try:
#             mail = imaplib.IMAP4_SSL(GMAIL_HOST, GMAIL_PORT)
#             mail.login(EMAIL, APP_PASSWORD)
#             mail.select('inbox')
#         except Exception as e:
#             notify_admin("ETL Mail Server Error",
#                          f"Failed to connect/login/select inbox.\nError: {str(e)}")
#             return JsonResponse({
#                 "message": "Failed to connect to mail server.",
#                 "error": str(e)
#             }, status=500)

#         for email_id, pdf_path in decrypted_info:
#             try:
#                 extract_and_insert_data_from_pdf(pdf_path, None)
#                 mail.store(email_id, '+FLAGS', '\\Seen')
#                 success_count += 1
#             except Exception as e:
#                 error_msg = f"Error processing email {email_id}:\n{e}"

#                 notify_admin("ETL PDF Processing Error", error_msg)

#         mail.logout()

#         return JsonResponse({
#             "message": "ETL job completed.",
#             "pdfs_processed": len(decrypted_info),
#             "successfully_processed": success_count
#         })

#     except Exception as e:
#         notify_admin("ETL System Error",
#                      f"Unexpected failure during ETL run.\nError: {str(e)}")
#         return JsonResponse({
#             "message": "Unexpected error during ETL run.",
#             "error": str(e)
#         }, status=500)


# from .services import process_gmail_pdfs
# @login_required
# def run_pdf_etl(request):
#     username = request.user.username if request.user.is_authenticated else None
#     process_gmail_pdfs(updated_by_username=username)
#     return JsonResponse({"status": "success", "message": "PDFs processed 232323."})


import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# from .services import process_gmail_pdfs
from .services import check_unread_mails,main

logger = logging.getLogger(__name__)




@login_required
def run_pdf_etl(request):

    count = check_unread_mails()
    if count == 0:
        print("📭 No unread mails")
        return JsonResponse({
            "status": "success",
            "message": "No unread mails."
        }, status=200)
    else:
        print(f"📧 You have {count} unread mails")
        main()
        return JsonResponse({
            "status": "success",
            "message": "Processed successfully."
        }, status=200)

    
    


# @login_required
# def run_pdf_etl(request):
#     username = request.user.username if request.user.is_authenticated else None

#     try:
#         # process_gmail_pdfs(updated_by_username=username)
#         process_gmail_pdfs()
#         return JsonResponse({
#             "status": "success",
#             "message": "PDFs processed successfully."
#         }, status=200)

#     except FileNotFoundError as e:
#         logger.error(f"Missing file error while processing PDFs: {e}")
#         return JsonResponse({
#             "status": "error",
#             "error_type": "FileNotFoundError",
#             "message": str(e)
#         }, status=400)

#     except PermissionError as e:
#         logger.error(f"Permission error while processing PDFs: {e}")
#         return JsonResponse({
#             "status": "error",
#             "error_type": "PermissionError",
#             "message": "Permission denied while accessing PDF files."
#         }, status=403)

#     except ValueError as e:
#         logger.error(f"Value error while processing PDFs: {e}")
#         return JsonResponse({
#             "status": "error",
#             "error_type": "ValueError",
#             "message": str(e)
#         }, status=400)

#     except Exception as e:
#         logger.exception("Unexpected error while processing PDFs")
#         return JsonResponse({
#             "status": "error",
#             "error_type": "Exception",
#             "message": "An unexpected error occurred while processing PDFs.",
#             "details": str(e)
#         }, status=500)




# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .models import CyberCellReport
# from datetime import datetime

# @api_view(['GET'])
# def cases_api(request):
#     cases_qs = CyberCellReport.objects.all()

#     cases = []
#     total_amount = 0

#     def parse_date(date_str, in_format=None, out_format="%Y-%m-%d"):
#         """Try parsing a date string and return formatted date, else return original"""
#         if not date_str:
#             return ""
#         try:
#             if in_format:
#                 dt = datetime.strptime(date_str, in_format)
#             else:
#                 # Try common formats
#                 for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
#                     try:
#                         dt = datetime.strptime(date_str, fmt)
#                         break
#                     except ValueError:
#                         continue
#                 else:
#                     return date_str  # give up
#             return dt.strftime(out_format)
#         except Exception:
#             return date_str

#     for c in cases_qs:
#         # Total fraud amount calculation
#         fraud_amt_str = str(c.total_fraudulent_amount).replace('₹', '').replace(',', '')
#         try:
#             amt = float(fraud_amt_str)
#         except ValueError:
#             amt = 0
#         total_amount += amt

#         # Append dict with formatted dates
#         cases.append({
#             'sno': c.sno,
#             'complaint_date': parse_date(c.complaint_date),
#             'mail_date': parse_date(c.mail_date),
#             'mail_month': parse_date(c.mail_date, out_format="%B"),  # month name
#             'amount': c.amount,
#             'reference_number': c.reference_number,
#             'police_station_address': c.police_station_address,
#             'account_number': c.account_number,
#             'name': c.name,
#             'mobile_number': c.mobile_number,
#             'email_id': c.email_id,
#             'status': c.status.title() if c.status else '',
#             'ageing_days': c.ageing_days,
#             'debit_from_bank': c.debit_from_bank.title() if c.debit_from_bank else '',
#             'region': c.region,
#             'utr_number': c.utr_number,
#             'utr_amount': c.utr_amount,
#             'transaction_datetime': parse_date(c.transaction_datetime, out_format="%Y-%m-%d %H:%M:%S"),
#             'total_fraudulent_amount': c.total_fraudulent_amount,
#             'updated_on': c.updated_on.strftime("%Y-%m-%d %H:%M") if c.updated_on else '',
#             'updated_by': str(c.updated_by) if c.updated_by else '',
#         })

#     return Response({
#         'cases': cases,
#         'total_amount': f'₹{total_amount:,.2f}'
#     })


# Usage inside your cases loop:
# complaint_date_parsed = parse_date(c.complaint_date)
# mail_date_parsed = parse_date(c.mail_date)
# mail_month_parsed = get_month(c.mail_date)
def format_indian_number(number, decimals=2):
    """
    Convert a number to Indian style format with commas.
    Example: 490028384.45 -> 49,00,28,384.45
    """
    if number is None:
        return f"0.{ '0'*decimals }"
    if "." not in str(number):
        print(type(number),number)
        number = number+".00"
        print(number)

    try:
        number = float(number)
    except (ValueError, TypeError):
        return str(number)

    # Split integer and decimal parts
    int_part, dec_part = divmod(number, 1)
    dec_part = round(dec_part * (10 ** decimals))  # handle decimals

    int_part_str = str(int(int_part))

    if len(int_part_str) <= 3:
        formatted_int = int_part_str
    else:
        last3 = int_part_str[-3:]
        rest = int_part_str[:-3]
        rest_groups = []
        while len(rest) > 2:
            rest_groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            rest_groups.insert(0, rest)
        formatted_int = ','.join(rest_groups) + ',' + last3

    # print(f"{formatted_int}.{dec_part:0{decimals}d}")
    return f"{formatted_int}.{dec_part:0{decimals}d}"

@login_required
@api_view(['GET'])
def cases_api(request):
    # Query all CyberCellReport records
    cases_qs = CyberCellReport.objects.all()

    cases = []
    total_amount = 0

    for c in cases_qs:
        from zoneinfo import ZoneInfo

        updated_on_ist = c.updated_on.astimezone(ZoneInfo("Asia/Kolkata"))
        formatted_time = updated_on_ist.strftime('%d-%m-%Y %I:%M:%S %p')


        fraud_amt_str = c.total_fraudulent_amount.replace(
            '₹', '').replace(',', '')
        try:
            amt = float(fraud_amt_str)
        except ValueError:
            amt = 0
        total_amount += amt

        cases.append({
            'sno': c.sno,
            'complaint_date': parse_date((c.complaint_date)),
            'mail_date': parse_date((c.mail_date)),
            'mail_month': c.mail_month,
            'amount': format_indian_number(c.amount),
            'reference_number': c.reference_number,
            'police_station_address': c.police_station_address,
            'account_number': c.account_number,
            'name': c.name,
            'mobile_number': c.mobile_number,
            'email_id': c.email_id,
            'status': c.status.title(),
            'ageing_days': c.ageing_days,
            'debit_from_bank': c.debit_from_bank.title() if c.debit_from_bank else '',
            'region': c.region,
            'utr_number': c.utr_number,
            'utr_amount': format_indian_number(c.utr_amount),
            'transaction_datetime': c.transaction_datetime,
            'total_fraudulent_amount': format_indian_number(c.total_fraudulent_amount),
            # 'updated_on': c.updated_on.strftime('%d-%m-%Y %H:%M:%S'),
            'updated_on': formatted_time,
            'updated_by': str(c.updated_by) if c.updated_by else '',
            "pdf_url": request.build_absolute_uri(c.pdf_file.url) if c.pdf_file else None,
            'lien_amount': format_indian_number(c.lien_amount) or 0,
            'remarks': c.remarks or ''

        })
    print(cases)    

    return Response({
        'cases': cases,
        'total_amount': f'₹{total_amount:,.2f}'
    })


# @login_required
# @api_view(['POST'])
# def update_case_status(request, sno):
#     new_status = request.data.get('status')
#     new_debit = request.data.get('debit_from_bank')

#     valid_statuses = [choice[0] for choice in CyberCellReport.STATUS_CHOICES]
#     valid_debits = [choice[0] for choice in CyberCellReport.DEBIT_CHOICES]

#     if new_status and new_status not in valid_statuses:
#         return Response({"error": f"Invalid status value. Allowed: {valid_statuses}"},
#                         status=drf_status.HTTP_400_BAD_REQUEST)

#     if new_debit and new_debit not in valid_debits:
#         return Response({"error": f"Invalid debit_from_bank value. Allowed: {valid_debits}"},
#                         status=drf_status.HTTP_400_BAD_REQUEST)

#     try:
#         case = CyberCellReport.objects.get(sno=sno)
#     except CyberCellReport.DoesNotExist:
#         return Response({"error": "Case not found"},
#                         status=drf_status.HTTP_404_NOT_FOUND)

#     if new_status:
#         case.status = new_status
#         if request.user.is_authenticated:
#             user = request.user
#             case.updated_by = user
#             case.updated_on = timezone.now()

#     if new_debit:
#         case.debit_from_bank = new_debit
#         if request.user.is_authenticated:
#             user = request.user
#             case.updated_by = user
#             case.updated_on = timezone.now()

#     case.save()

#     return Response({
#         "message": "Case updated successfully",
#         "updated_case": {
#             "sno": case.sno,
#             "status": case.status,
#             "debit_from_bank": case.debit_from_bank
#         }
#     })


# @login_required
# @api_view(['POST'])
# def update_case_status(request, sno):
#     new_status = request.data.get('status')
#     new_debit = request.data.get('debit_from_bank')
#     new_lien = request.data.get('lien_amount')
#     new_remarks = request.data.get('remarks')

#     valid_statuses = [choice[0] for choice in CyberCellReport.STATUS_CHOICES]
#     valid_debits = [choice[0] for choice in CyberCellReport.DEBIT_CHOICES]

#     if new_status and new_status not in valid_statuses:
#         return Response({"error": f"Invalid status value. Allowed: {valid_statuses}"},
#                         status=drf_status.HTTP_400_BAD_REQUEST)

#     if new_debit and new_debit not in valid_debits:
#         return Response({"error": f"Invalid debit_from_bank value. Allowed: {valid_debits}"},
#                         status=drf_status.HTTP_400_BAD_REQUEST)

#     try:
#         case = CyberCellReport.objects.get(sno=sno)
#     except CyberCellReport.DoesNotExist:
#         return Response({"error": "Case not found"},
#                         status=drf_status.HTTP_404_NOT_FOUND)

#     if new_status:
#         case.status = new_status
#     if new_debit:
#         case.debit_from_bank = new_debit
#     if new_lien is not None:
#         case.lien_amount = new_lien
#     if new_remarks is not None:
#         case.remarks = new_remarks

#     case.updated_by = request.user
#     case.save()

#     return Response({
#         "message": "Case updated successfully",
#         "updated_case": {
#             "sno": case.sno,
#             "status": case.status,
#             "debit_from_bank": case.debit_from_bank,
#             "lien_amount": case.lien_amount,
#             "remarks": case.remarks,
#         }
#     })



@login_required
@api_view(['POST'])
def update_case_status(request, sno):
    new_status = request.data.get('status')
    new_debit = request.data.get('debit_from_bank')
    new_lien = request.data.get('lien_amount')
    new_remarks = request.data.get('remarks')
    new_utr = request.data.get('utr_number')   # ✅ New field

    valid_statuses = [choice[0] for choice in CyberCellReport.STATUS_CHOICES]
    valid_debits = [choice[0] for choice in CyberCellReport.DEBIT_CHOICES]

    if new_status and new_status not in valid_statuses:
        return Response({"error": f"Invalid status value. Allowed: {valid_statuses}"},
                        status=drf_status.HTTP_400_BAD_REQUEST)

    if new_debit and new_debit not in valid_debits:
        return Response({"error": f"Invalid debit_from_bank value. Allowed: {valid_debits}"},
                        status=drf_status.HTTP_400_BAD_REQUEST)

    try:
        case = CyberCellReport.objects.get(sno=sno)
    except CyberCellReport.DoesNotExist:
        return Response({"error": "Case not found"},
                        status=drf_status.HTTP_404_NOT_FOUND)

    if new_status:
        case.status = new_status
    if new_debit:
        case.debit_from_bank = new_debit
    if new_lien is not None:
        case.lien_amount = new_lien
    if new_remarks is not None:
        case.remarks = new_remarks
    if new_utr is not None:   # ✅ save utr_number if provided
        case.utr_number = new_utr

    case.updated_by = request.user
    case.save()

    return Response({
        "message": "Case updated successfully",
        "updated_case": {
            "sno": case.sno,
            "status": case.status,
            "debit_from_bank": case.debit_from_bank,
            "lien_amount": case.lien_amount,
            "remarks": case.remarks,
            "utr_number": case.utr_number,   # ✅ include in response
        }
    })
