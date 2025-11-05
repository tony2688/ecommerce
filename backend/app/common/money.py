from decimal import Decimal


def format_money(amount: Decimal | float | int) -> str:
    d = Decimal(str(amount))
    return f"{d.quantize(Decimal('0.01'))}"