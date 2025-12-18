def clean_odometer(text: str) -> int:
    """Перетворює '95 тис. км' -> 95000"""
    if not text:
        return 0
    text = text.lower().replace(" ", "")
    try:
        if "тис" in text:
            num = float(text.split("тис")[0])
            return int(num * 1000)
        return int(''.join(filter(str.isdigit, text)))
    except ValueError:
        return 0

def clean_price(text: str) -> int:
    """'10 500 $' -> 10500"""
    if not text:
        return 0
    return int(''.join(filter(str.isdigit, text)))
