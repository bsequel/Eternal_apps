# email_parser/pdf_parser.py
import re
import json
import pdfplumber
from pathlib import Path

def extract_structured_data_from_pdf(pdf_path, output_json_path=None):
    pdf_path = Path(pdf_path)
    if output_json_path is None:
        output_json_path = pdf_path.with_suffix(".json")

    def extract_text_lines(path):
        with pdfplumber.open(path) as pdf:
            all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
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
            cyber_data["Address"] = words[-1]
        elif "State /District /Police Station" in line:
            cyber_data["Police_Station_Address"] = line.split("State /District /Police Station")[-1].strip()
        elif "Acknowledgement No." in line and words:
            cyber_data["RefNo"] = words[-1]
        elif "Name" in line and is_valid(line):
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
            line_dict = {
                'ComplaintDate': y[0][7] + ' ' + y[1][8],
                'Account_No': y[0][3],
                'Amount': y[4][3],
                'Region': y[0][-1],
                'UTR_No': y[0][4],
                'UTR_Amount': y[1][6],
                'Transaction_Date': y[0][6] + ' ' + y[1][7]
            }
            line_items_list.append(line_dict)
        except IndexError:
            continue

    cyber_data["LineItems"] = line_items_list

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(cyber_data, f, indent=2, ensure_ascii=False)

    print(f"\u2705 Structured data saved to: {output_json_path}")
    return output_json_path