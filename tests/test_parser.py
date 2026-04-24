"""Tests for shopping list parser (structured format only)."""

import pytest
from coffee_ordering.parser import ShoppingListParser


def test_parse_skips_empty_lines():
    """Test that empty lines are skipped."""
    parser = ShoppingListParser()
    text = """
    bali-karana|453|2

    etiopie-tabe-burka|459|1
    """

    items = parser.parse(text)

    assert len(items) == 2


def test_parse_skips_comments():
    """Test that comments are skipped."""
    parser = ShoppingListParser()
    text = """
    bali-karana|453|2
    # This is a comment
    etiopie-tabe-burka|459|1
    """

    items = parser.parse(text)

    assert len(items) == 2


def test_parse_structured_format():
    """Test parsing structured format: product_id|variant_id|quantity."""
    parser = ShoppingListParser()
    text = """
    bali-karana|453|2
    brazilie-vargem-alegre|456|1
    etiopie-tabe-burka|459
    """

    items = parser.parse(text)

    assert len(items) == 3

    # First item
    assert items[0].quantity == 2
    assert items[0].preferences["product_id"] == "bali-karana"
    assert items[0].preferences["variant_id"] == "453"

    # Second item
    assert items[1].quantity == 1
    assert items[1].preferences["product_id"] == "brazilie-vargem-alegre"
    assert items[1].preferences["variant_id"] == "456"

    # Third item (no quantity, defaults to 1)
    assert items[2].quantity == 1
    assert items[2].preferences["product_id"] == "etiopie-tabe-burka"
    assert items[2].preferences["variant_id"] == "459"


def test_parse_structured_format_with_spaces():
    """Test structured format with spaces around separators."""
    parser = ShoppingListParser()
    text = "product-123 | variant-456 | 3"

    items = parser.parse(text)

    assert len(items) == 1
    assert items[0].quantity == 3
    assert items[0].preferences["product_id"] == "product-123"
    assert items[0].preferences["variant_id"] == "variant-456"


def test_parse_invalid_format_no_pipe():
    """Test that invalid format (no pipe) raises error."""
    parser = ShoppingListParser()
    text = "Ethiopian Natural 250g"

    with pytest.raises(ValueError, match="Invalid format"):
        parser.parse(text)


def test_parse_invalid_format_only_product_id():
    """Test that invalid format (only product_id) raises error."""
    parser = ShoppingListParser()
    text = "bali-karana|"

    with pytest.raises(ValueError, match="variant_id cannot be empty"):
        parser.parse(text)


def test_parse_invalid_quantity():
    """Test that invalid quantity raises error."""
    parser = ShoppingListParser()
    text = "bali-karana|453|abc"

    with pytest.raises(ValueError, match="quantity must be a number"):
        parser.parse(text)


def test_parse_negative_quantity():
    """Test that negative quantity raises error."""
    parser = ShoppingListParser()
    text = "bali-karana|453|-1"

    with pytest.raises(ValueError, match="quantity must be positive"):
        parser.parse(text)
