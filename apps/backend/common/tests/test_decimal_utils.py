"""
Tests for decimal_utils module.

CRITICAL: These tests ensure financial precision is maintained.
"""

from decimal import Decimal
import pytest

from common.decimal_utils import (
    money,
    display_money,
    sum_money,
    multiply_money,
    divide_money,
    calculate_percentage,
    calculate_gst,
    extract_gst_from_inclusive,
    Money,
    MONEY_PLACES,
)


class TestMoneyFunction:
    """Tests for the money() function."""
    
    def test_converts_string_to_decimal(self):
        result = money("100.50")
        assert result == Decimal("100.5000")
        
    def test_converts_integer_to_decimal(self):
        result = money(100)
        assert result == Decimal("100.0000")
        
    def test_converts_decimal_to_decimal(self):
        result = money(Decimal("100.5"))
        assert result == Decimal("100.5000")
        
    def test_rejects_float(self):
        with pytest.raises(TypeError, match="Float.*is not allowed"):
            money(100.50)
            
    def test_quantizes_to_4dp(self):
        result = money("100.99999")
        assert result == Decimal("101.0000")
        
    def test_rounds_half_up(self):
        result = money("100.00005")
        assert result == Decimal("100.0001")
        
    def test_handles_zero(self):
        result = money("0")
        assert result == Decimal("0.0000")
        
    def test_handles_empty_string(self):
        with pytest.raises(ValueError):
            money("")


class TestDisplayMoney:
    """Tests for the display_money() function."""
    
    def test_formats_to_2dp(self):
        result = display_money("100.5")
        assert result == "100.50"
        
    def test_rounds_to_2dp(self):
        result = display_money("100.999")
        assert result == "101.00"
        
    def test_rejects_float(self):
        with pytest.raises(TypeError):
            display_money(100.50)


class TestSumMoney:
    """Tests for the sum_money() function."""
    
    def test_sums_list_of_values(self):
        result = sum_money(["10.00", "20.50", "30.25"])
        assert result == Decimal("60.7500")
        
    def test_handles_empty_list(self):
        result = sum_money([])
        assert result == Decimal("0.0000")
        
    def test_maintains_precision(self):
        result = sum_money(["0.0001", "0.0001", "0.0001"])
        assert result == Decimal("0.0003")


class TestMultiplyMoney:
    """Tests for the multiply_money() function."""
    
    def test_multiplies_two_values(self):
        result = multiply_money("100.00", "0.09")  # 9% GST
        assert result == Decimal("9.0000")
        
    def test_quantizes_result(self):
        result = multiply_money("33.33", "0.09")
        # 33.33 * 0.09 = 2.9997
        assert result == Decimal("3.0000")


class TestDivideMoney:
    """Tests for the divide_money() function."""
    
    def test_divides_two_values(self):
        result = divide_money("100.00", "4")
        assert result == Decimal("25.0000")
        
    def test_raises_on_divide_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            divide_money("100.00", "0")


class TestCalculatePercentage:
    """Tests for the calculate_percentage() function."""
    
    def test_calculates_percentage(self):
        result = calculate_percentage("1000.00", "9")  # 9% of 1000
        assert result == Decimal("90.0000")
        
    def test_calculates_gst(self):
        result = calculate_percentage("1000.00", "9")
        assert result == Decimal("90.0000")


class TestCalculateGST:
    """Tests for GST calculations."""
    
    def test_calculates_9_percent_gst(self):
        result = calculate_gst("1000.00")
        assert result == Decimal("90.0000")
        
    def test_gst_on_zero(self):
        result = calculate_gst("0")
        assert result == Decimal("0.0000")


class TestExtractGSTFromInclusive:
    """Tests for extracting GST from inclusive amounts."""
    
    def test_extracts_gst_correctly(self):
        net, gst = extract_gst_from_inclusive("1090.00")
        assert net == Decimal("1000.0000")
        assert gst == Decimal("90.0000")
        
    def test_handles_rounding(self):
        # $10.90 inclusive = $10.00 + $0.90 GST
        net, gst = extract_gst_from_inclusive("10.90")
        assert net == Decimal("10.0000")
        assert gst == Decimal("0.9000")


class TestMoneyClass:
    """Tests for the Money convenience class."""
    
    def test_creation(self):
        m = Money("100.00")
        assert m.value == Decimal("100.0000")
        
    def test_addition(self):
        m1 = Money("100.00")
        m2 = Money("50.00")
        result = m1 + m2
        assert result.value == Decimal("150.0000")
        
    def test_subtraction(self):
        m1 = Money("100.00")
        m2 = Money("30.00")
        result = m1 - m2
        assert result.value == Decimal("70.0000")
        
    def test_multiplication(self):
        m = Money("100.00")
        result = m * Decimal("0.09")
        assert result.value == Decimal("9.0000")
        
    def test_division(self):
        m = Money("100.00")
        result = m / Decimal("4")
        assert result.value == Decimal("25.0000")
        
    def test_comparison(self):
        m1 = Money("100.00")
        m2 = Money("100.00")
        m3 = Money("50.00")
        
        assert m1 == m2
        assert m1 > m3
        assert m3 < m1
        
    def test_to_display(self):
        m = Money("100.5")
        assert m.to_display() == "100.50"
