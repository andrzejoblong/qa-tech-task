"""Money helpers. Amounts are Decimal so that comparisons are exact to the cent."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def parse_euro(text: str) -> Decimal:
    """Turn a displayed amount such as '€24.50' or 'Balance: €-3.10' into a Decimal."""
    return Decimal(text.split("€", 1)[1].strip())


def to_decimal(number: float) -> Decimal:
    """Convert a JSON number without carrying over binary floating-point noise."""
    return Decimal(str(number))


def payout(stake: Decimal, odds: Decimal) -> Decimal:
    """Potential payout as the specification defines it: stake × odds, to the cent."""
    return (stake * odds).quantize(CENT, rounding=ROUND_HALF_UP)
