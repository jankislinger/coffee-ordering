"""Tests for data models."""

from decimal import Decimal

from coffee_ordering.models import CartItem, Product, ShoppingListItem, Variant


def test_product_creation():
    """Test creating a product."""
    variant = Variant(
        id="variant-1",
        name="250g",
        price=Decimal("18.50"),
    )

    product = Product(
        id="test-1",
        name="Ethiopian Natural",
        roaster="doubleshot",
        available=True,
        variants=[variant],
    )

    assert product.id == "test-1"
    assert product.name == "Ethiopian Natural"
    assert len(product.variants) == 1
    assert product.variants[0].price == Decimal("18.50")


def test_cart_item_creation():
    """Test cart item creation."""
    cart_item = CartItem(
        product_id="test-1",
        variant_id="variant-1",
        quantity=2,
    )

    assert cart_item.product_id == "test-1"
    assert cart_item.variant_id == "variant-1"
    assert cart_item.quantity == 2


def test_shopping_list_item_defaults():
    """Test shopping list item defaults."""
    item = ShoppingListItem(raw_text="Ethiopian coffee")

    assert item.quantity == 1
    assert item.preferences == {}
