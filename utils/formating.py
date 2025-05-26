# Где-то в начале файла (например, после импортов)
def format_amount(amount: float) -> str:
    """Форматирует число с разделителем тысяч и двумя знаками после запятой"""
    rounded = round(amount + 1e-8, 2)
    return "{:,.2f}".format(rounded).replace(",", " ").replace(".", ",")
