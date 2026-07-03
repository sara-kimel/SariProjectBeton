from typing import Optional

def double_price_from_string(text: Optional[str]) -> Optional[str]:
    """מכפיל את המחיר שמופיע בתוך string ב-2"""
    if text is None:
        return None

    import re
    match = re.search(r"\d+(\.\d+)?", text)
    if match:
        price = float(match.group())
        return str(price * 2)  # שמירה כמחרוזת כדי להתאים ל-DB
    return None