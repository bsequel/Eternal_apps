from datetime import datetime
def parse_date(date_str):
    """Detect and format several date formats"""
    if not date_str:
        return ""
    for fmt in [
        "%d/%m/%Y %I:%M:%p",  # 20/03/2025 12:48:PM
        "%A, %B %d, %Y %I:%M:%S %p GMT",  # Tuesday, April 1, 2025 4:56:53 PM GMT
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y"
    ]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%d-%m-%Y')
        except Exception:
            continue
    return date_str  # fallback

def get_month(date_str):
    for fmt in [
        "%A, %B %d, %Y %I:%M:%S %p GMT",
        "%d/%m/%Y %I:%M:%p",
        "%Y-%m-%d"
    ]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%B")
        except Exception:
            continue
    return ""
