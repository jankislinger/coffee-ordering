"""Cart management."""

from coffee_ordering.models import CartItem, Product


class CartManager:
    """Manage shopping cart operations."""

    def __init__(self):
        """Initialize cart manager."""
        self.items: list[CartItem] = []

    def add_item(self, product: Product, quantity: int = 1, variant_id: str | None = None):
        """
        Add item to cart.

        Args:
            product: Product to add
            quantity: Quantity to add
            variant_id: Optional variant ID (uses first variant if not specified)
        """
        # Determine variant_id - use provided or first variant
        final_variant_id = variant_id
        if not final_variant_id and product.variants:
            final_variant_id = product.variants[0].id

        # Check if item already exists in cart
        for item in self.items:
            if item.product_id == product.id and item.variant_id == final_variant_id:
                item.quantity += quantity
                return

        # Add new item
        cart_item = CartItem(
            product_id=product.id,
            variant_id=final_variant_id,
            quantity=quantity,
        )
        self.items.append(cart_item)

    def remove_item(self, product_id: str, variant_id: str):
        """
        Remove item from cart.

        Args:
            product_id: Product ID to remove
            variant_id: Variant ID
        """
        self.items = [
            item
            for item in self.items
            if not (item.product_id == product_id and item.variant_id == variant_id)
        ]

    def update_quantity(self, product_id: str, quantity: int, variant_id: str):
        """
        Update item quantity.

        Args:
            product_id: Product ID
            quantity: New quantity
            variant_id: Variant ID
        """
        for item in self.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                if quantity <= 0:
                    self.remove_item(product_id, variant_id)
                else:
                    item.quantity = quantity
                return

    def clear(self):
        """Clear all items from cart."""
        self.items = []

    @property
    def item_count(self) -> int:
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items)


