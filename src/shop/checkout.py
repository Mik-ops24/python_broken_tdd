"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _is_int_text(value: str) -> bool:
    stripped = value.strip()
    if stripped == "":
        return False
    if stripped[0] in "+-":
        return stripped[1:].isdecimal()
    return stripped.isdecimal()


def _tier_discount_percent(unit_count: int) -> int:
    discount_percent = 0
    for threshold, percent in TIER_DISCOUNTS:
        if unit_count >= threshold:
            discount_percent = percent
    return discount_percent


def _validate_destination(promo_code: str, shipping_city: str) -> str | None:
    if promo_code and promo_code not in PROMO_CODES:
        return "unknown promo code"
    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "unsupported shipping city"
    return None


def _missing_line_key(line: dict[str, str]) -> str:
    for key in REQUIRED_LINE_KEYS:
        if key not in line:
            return key
    return ""


def _validate_line(line: dict[str, str], line_number: int) -> str | None:
    missing_key = _missing_line_key(line)
    if missing_key:
        return f"line {line_number} is missing {missing_key}"

    if line["sku"] == "":
        return "sku is empty"

    if not _is_int_text(line["qty"]):
        return "quantity is not a number"
    qty = int(line["qty"])
    if qty <= 0:
        return "quantity must be positive"

    if not _is_int_text(line["unit_price_kopecks"]):
        return "unit price is not a number"
    unit_price = int(line["unit_price_kopecks"])
    if unit_price < 0:
        return "unit price must not be negative"

    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "order has no lines"

    destination_problem = _validate_destination(promo_code, shipping_city)
    if destination_problem is not None:
        return destination_problem

    seen_skus: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        line_problem = _validate_line(line, line_number)
        if line_problem is not None:
            return line_problem

        sku = line["sku"]
        if sku in seen_skus:
            return "sku is duplicated"
        seen_skus.add(sku)
    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = 0
    unit_count = 0

    for line in lines:
        qty = int(line["qty"])
        unit_price = int(line["unit_price_kopecks"])
        subtotal += qty * unit_price
        unit_count += qty

    promo_discount_percent = PROMO_CODES.get(promo_code, 0)
    tier_discount_percent = _tier_discount_percent(unit_count)
    discount_percent = max(promo_discount_percent, tier_discount_percent)
    discount_percent = min(discount_percent, MAX_DISCOUNT_PERCENT)

    discount = percent_of(subtotal, discount_percent)
    discounted_subtotal = subtotal - discount
    shipping = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS

    base = discounted_subtotal + shipping
    vat = percent_of(base, VAT_PERCENT)

    return base + vat
