"""
Decimal safety utilities for financial calculations.

CRITICAL: All monetary calculations MUST use these utilities to ensure
precision and prevent floating-point errors.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, localcontext
from contextlib import contextmanager
from typing import Union, Iterable


# Precision constants
MONEY_PLACES = Decimal("0.0001")  # 4 decimal places for internal storage
DISPLAY_PLACES = Decimal("0.01")   # 2 decimal places for display


def money(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Convert any numeric input to a Decimal at 4 decimal places.
    
    REJECTS float inputs in strict mode to prevent precision loss.
    
    Args:
        value: The value to convert (str, int, or Decimal)
        
    Returns:
        Decimal quantized to 4 decimal places
        
    Raises:
        TypeError: If float is passed (to prevent precision loss)
        ValueError: If value cannot be converted to Decimal
        
    Example:
        >>> money("100.50")
        Decimal('100.5000')
        >>> money(100)
        Decimal('100.0000')
    """
    if isinstance(value, float):
        raise TypeError(
            f"Float {value} is not allowed for monetary values. "
            f"Use str or Decimal: money('{value}')"
        )
    
    try:
        with localcontext() as ctx:
            ctx.rounding = ROUND_HALF_UP
            ctx.traps[InvalidOperation] = True
            return Decimal(str(value)).quantize(MONEY_PLACES)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot convert {value!r} to money: {e}")


def display_money(value: Union[str, int, float, Decimal]) -> str:
    """
    Format a monetary value to 2 decimal places for display.
    
    Args:
        value: The value to format
        
    Returns:
        String formatted to 2 decimal places
        
    Example:
        >>> display_money("100.5")
        '100.50'
        >>> display_money(Decimal("100.999"))
        '101.00'
    """
    if isinstance(value, float):
        raise TypeError(
            f"Float {value} is not allowed. Use str or Decimal."
        )
    
    try:
        with localcontext() as ctx:
            ctx.rounding = ROUND_HALF_UP
            return str(Decimal(str(value)).quantize(DISPLAY_PLACES))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot format {value!r}: {e}")


def sum_money(values: Iterable[Union[str, int, Decimal]]) -> Decimal:
    """
    Sum an iterable of monetary values with proper precision.
    
    Args:
        values: Iterable of values to sum
        
    Returns:
        Sum quantized to 4 decimal places
        
    Example:
        >>> sum_money(["10.00", "20.50", "30.25"])
        Decimal('60.7500')
    """
    total = Decimal("0")
    for value in values:
        total += money(value)
    return total.quantize(MONEY_PLACES)


def multiply_money(a: Union[str, int, Decimal], 
                   b: Union[str, int, Decimal]) -> Decimal:
    """
    Multiply two monetary values with proper precision.
    
    Args:
        a: First value
        b: Second value
        
    Returns:
        Product quantized to 4 decimal places
        
    Example:
        >>> multiply_money("100.00", "0.09")  # 9% GST
        Decimal('9.0000')
    """
    result = money(a) * money(b)
    return result.quantize(MONEY_PLACES)


def divide_money(dividend: Union[str, int, Decimal],
                 divisor: Union[str, int, Decimal]) -> Decimal:
    """
    Divide two monetary values with proper precision.
    
    Args:
        dividend: Value to divide
        divisor: Value to divide by
        
    Returns:
        Quotient quantized to 4 decimal places
        
    Raises:
        ZeroDivisionError: If divisor is zero
        
    Example:
        >>> divide_money("100.00", "4")
        Decimal('25.0000')
    """
    if money(divisor) == Decimal("0"):
        raise ZeroDivisionError("Cannot divide by zero")
    
    result = money(dividend) / money(divisor)
    return result.quantize(MONEY_PLACES)


def calculate_percentage(base: Union[str, int, Decimal],
                        percentage: Union[str, int, Decimal]) -> Decimal:
    """
    Calculate a percentage of a base amount.
    
    Args:
        base: Base amount
        percentage: Percentage (e.g., 9 for 9%)
        
    Returns:
        Percentage of base quantized to 4 decimal places
        
    Example:
        >>> calculate_percentage("1000.00", "9")  # 9% GST
        Decimal('90.0000')
    """
    base_dec = money(base)
    pct_dec = money(percentage)
    result = base_dec * (pct_dec / Decimal("100"))
    return result.quantize(MONEY_PLACES)


def round_half_up(value: Union[str, int, Decimal], 
                  decimal_places: int = 4) -> Decimal:
    """
    Round a value to specified decimal places using ROUND_HALF_UP.
    
    Args:
        value: Value to round
        decimal_places: Number of decimal places (default: 4)
        
    Returns:
        Rounded Decimal
    """
    places = Decimal("0.1") ** decimal_places
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        return Decimal(str(value)).quantize(places)


@contextmanager
def decimal_context(precision: int = 28, rounding=None):
    """
    Context manager for Decimal operations with custom precision and rounding.
    
    Args:
        precision: Decimal precision (default: 28)
        rounding: Rounding mode (default: ROUND_HALF_UP)
        
    Example:
        >>> with decimal_context():
        ...     result = Decimal("1") / Decimal("3")
    """
    if rounding is None:
        rounding = ROUND_HALF_UP
        
    with localcontext() as ctx:
        ctx.prec = precision
        ctx.rounding = rounding
        ctx.traps[InvalidOperation] = True
        yield


# Convenience function for GST calculations (9% Singapore rate)
GST_RATE = Decimal("0.09")
GST_FRACTION = Decimal("9") / Decimal("109")  # For GST-inclusive amounts


def calculate_gst(net_amount: Union[str, int, Decimal]) -> Decimal:
    """
    Calculate 9% GST on a net amount.
    
    Args:
        net_amount: Amount before GST
        
    Returns:
        GST amount quantized to 4 decimal places
        
    Example:
        >>> calculate_gst("1000.00")
        Decimal('90.0000')
    """
    return multiply_money(net_amount, GST_RATE)


def extract_gst_from_inclusive(inclusive_amount: Union[str, int, Decimal]) -> tuple[Decimal, Decimal]:
    """
    Extract GST and net amount from a GST-inclusive total.
    
    Uses the formula: GST = Total * (9/109)
    
    Args:
        inclusive_amount: Total amount including GST
        
    Returns:
        Tuple of (net_amount, gst_amount)
        
    Example:
        >>> extract_gst_from_inclusive("1090.00")
        (Decimal('1000.0000'), Decimal('90.0000'))
    """
    total = money(inclusive_amount)
    gst = (total * GST_FRACTION).quantize(MONEY_PLACES)
    net = (total - gst).quantize(MONEY_PLACES)
    return net, gst


class Money:
    """
    Convenience class for monetary values with operator overloading.
    
    Example:
        >>> m1 = Money("100.00")
        >>> m2 = Money("50.00")
        >>> m1 + m2
        Money('150.0000')
        >>> m1 * Decimal("0.09")
        Money('9.0000')
    """
    
    def __init__(self, value: Union[str, int, Decimal]):
        self._value = money(value)
    
    @property
    def value(self) -> Decimal:
        return self._value
    
    def __add__(self, other) -> "Money":
        if isinstance(other, Money):
            return Money(self._value + other._value)
        return Money(self._value + money(other))
    
    def __sub__(self, other) -> "Money":
        if isinstance(other, Money):
            return Money(self._value - other._value)
        return Money(self._value - money(other))
    
    def __mul__(self, other) -> "Money":
        if isinstance(other, Money):
            result = self._value * other._value
        else:
            result = self._value * money(other)
        return Money(result.quantize(MONEY_PLACES))
    
    def __truediv__(self, other) -> "Money":
        if isinstance(other, Money):
            divisor = other._value
        else:
            divisor = money(other)
        if divisor == Decimal("0"):
            raise ZeroDivisionError("Cannot divide by zero")
        result = self._value / divisor
        return Money(result.quantize(MONEY_PLACES))
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Money):
            return self._value == other._value
        return self._value == money(other)
    
    def __lt__(self, other) -> bool:
        if isinstance(other, Money):
            return self._value < other._value
        return self._value < money(other)
    
    def __le__(self, other) -> bool:
        if isinstance(other, Money):
            return self._value <= other._value
        return self._value <= money(other)
    
    def __gt__(self, other) -> bool:
        if isinstance(other, Money):
            return self._value > other._value
        return self._value > money(other)
    
    def __ge__(self, other) -> bool:
        if isinstance(other, Money):
            return self._value >= other._value
        return self._value >= money(other)
    
    def __repr__(self) -> str:
        return f"Money('{self._value}')"
    
    def __str__(self) -> str:
        return str(self._value)
    
    def to_display(self) -> str:
        """Return value formatted to 2 decimal places for display."""
        return display_money(self._value)
