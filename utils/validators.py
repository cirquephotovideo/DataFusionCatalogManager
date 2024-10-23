import re

def validate_ean13(barcode: str) -> bool:
    """Validate EAN-13 barcode"""
    if not barcode or not barcode.isdigit() or len(barcode) != 13:
        return False
    
    total = 0
    for i in range(12):
        digit = int(barcode[i])
        total += digit * (3 if (i % 2) else 1)
    
    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(barcode[-1])

def validate_article_code(code: str) -> bool:
    """Validate article code format"""
    return bool(re.match(r'^[A-Za-z0-9\-_]{1,50}$', code))

def validate_required_fields(data: dict) -> tuple[bool, list]:
    """Validate required catalog fields"""
    required_fields = ['article_code', 'barcode', 'brand', 'description']
    missing_fields = [field for field in required_fields if not data.get(field)]
    return len(missing_fields) == 0, missing_fields
