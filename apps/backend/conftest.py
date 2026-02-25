"""
Pytest configuration and fixtures for LedgerSG.
"""

import pytest
from decimal import Decimal


@pytest.fixture
def sample_money():
    """Sample decimal money value."""
    return Decimal("100.0000")


@pytest.fixture
def sample_gst_amount():
    """Sample GST amount (9% of 100)."""
    return Decimal("9.0000")


@pytest.fixture
def sample_inclusive_amount():
    """Sample GST-inclusive amount."""
    return Decimal("109.0000")
