"""Base roaster client interface."""

from abc import ABC, abstractmethod

from coffee_ordering.models import CartItem, Product


class RoasterClient(ABC):
    """Abstract base class for roaster clients."""

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize roaster client.

        Args:
            **kwargs: Client-specific configuration
        """

    @abstractmethod
    def get_products(self) -> list[Product]:
        """
        Fetch all available products from the roaster.

        Returns:
            List of products
        """

    @abstractmethod
    def add_to_cart(self, items: list[CartItem], products: list[Product]) -> str:
        """
        Add items to the shopping cart.

        Args:
            items: List of cart items to add (contains product_id, variant_id, quantity)
            products: List of available products (for looking up product details)

        Returns:
            Cart URL for checkout
        """

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the roaster's website.

        Uses credentials from instance variables (e.g., self.username, self.password).

        Returns:
            True if authentication was successful, False otherwise
        """

    @abstractmethod
    def get_cart_url(self) -> str:
        """
        Get the cart URL for the roaster.

        Returns:
            Cart URL
        """

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    @abstractmethod
    def close(self):
        """Close client and cleanup resources."""
