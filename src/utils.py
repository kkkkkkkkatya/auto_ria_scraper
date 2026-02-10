import re  # Додай цей імпорт на самому початку файлу!


def clean_odometer(text: str) -> int:
    """
    Перетворює '95 тис. км' -> 95000
    '257\n тис. км' -> 257000
    None -> 0
    """
    if not text:
        return 0

    # 1. Прибираємо все зайве, залишаємо нормальний рядок
    # lower() - маленькі літери
    # replace - прибираємо нерозривні пробіли
    # strip - прибираємо пробіли з країв
    text = text.lower().replace('\xa0', ' ').strip()

    try:
        if "тис" in text:
            # Вирізаємо число перед словом "тис"
            # re.findall знайде всі цифри (і дробові теж)
            numbers = re.findall(r"[\d\s\.,]+", text)
            if numbers:
                # Беремо перше знайдене число, замінюємо кому на крапку, видаляємо пробіли
                raw_num = numbers[0].replace(",", ".").replace(" ", "")
                return int(float(raw_num) * 1000)

        # Якщо просто цифри (наприклад "145000 км")
        digits = ''.join(filter(str.isdigit, text))
        return int(digits) if digits else 0

    except Exception:
        return 0


def clean_price(text: str) -> int:
    """
    '10 500 $' -> 10500
    None -> 0
    """
    if not text:
        return 0
    digits = ''.join(filter(str.isdigit, text))

    if not digits:
        return 0

    return int(digits)
