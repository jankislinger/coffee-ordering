"""DoubleShot.cz roaster client implementation."""

import os
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from coffee_ordering.models import CartItem, Product, Variant
from coffee_ordering.roasters.base import RoasterClient


class DoubleShotClient(RoasterClient):
    """Client for doubleshot.cz roaster."""

    BASE_URL = "https://www.doubleshot.cz"

    def __init__(self, username: str = "", password: str = "", **kwargs):
        """
        Initialize DoubleShot client.

        Args:
            username: Optional username for authentication (defaults to DOUBLESHOT_USERNAME env var)
            password: Optional password for authentication (defaults to DOUBLESHOT_PASSWORD env var)
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        # Use provided credentials or fall back to environment variables
        self.username = username or os.getenv("DOUBLESHOT_USERNAME", "")
        self.password = password or os.getenv("DOUBLESHOT_PASSWORD", "")
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        self.timeout = 30.0

    def get_products(self) -> list[Product]:
        """
        Fetch all available products from DoubleShot.

        This method scrapes the product listing pages and extracts
        product information from HTML.

        Returns:
            List of products
        """
        products = []

        # Fetch the coffee products page (English)
        url = f"{self.BASE_URL}/en/taxons/coffee"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Find all product boxes
        product_boxes = soup.select(".productBox")

        for box in product_boxes:
            # Get product title
            title = box.get("title", "").strip()
            if not title:
                continue

            # Get product link
            link = box.select_one("a")
            if not link:
                continue

            href = link.get("href", "")
            if not href.startswith("/en/products/"):
                continue

            # Extract slug from href
            slug = href.replace("/en/products/", "")

            # Get product details from the product page
            product = self._get_product_details(slug)
            if product:
                products.append(product)

        return products

    def add_to_cart(self, items: list[CartItem], products: list[Product]) -> str:
        """
        Add items to the DoubleShot shopping cart.

        Args:
            items: List of cart items to add
            products: List of available products (for looking up product details)

        Returns:
            Cart URL for checkout
        """
        # Create product lookup map
        products_map = {p.id: p for p in products}

        for item in items:
            # Get product from map
            product = products_map.get(item.product_id)
            if not product:
                print(f"Warning: Product {item.product_id} not found")
                continue

            # Extract slug from product URL or use product ID
            slug = product.url.split("/products/")[-1] if product.url else product.id

            # Get the product page to extract form data
            product_url = f"{self.BASE_URL}/en/products/{slug}"
            response = self.session.get(product_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Find the add to cart form
            form = soup.select_one('form[name="sylius_add_to_cart"]')
            if not form:
                print(f"Warning: Could not find add to cart form for {slug}")
                continue

            # Extract form action and product ID
            action = form.get("action", "")
            if not action:
                print(f"Warning: No form action found for {slug}")
                continue

            # Get CSRF token
            token_input = form.select_one('input[name="sylius_add_to_cart[_token]"]')
            csrf_token = token_input.get("value", "") if token_input else ""

            if not csrf_token:
                print(f"Warning: No CSRF token found for {slug}")
                continue

            # Get packaging and purchase_type from variant
            packaging = "300g"  # Default
            purchase_type = "one-time"  # Default

            # If variant_id is provided, extract packaging/purchase_type from page
            if item.variant_id:
                variants_div = soup.select_one("#sylius-variants-pricing")
                if variants_div:
                    variant_elem = variants_div.select_one(f'[data-variant="{item.variant_id}"]')
                    if variant_elem:
                        packaging = variant_elem.get("data-packaging", packaging)
                        purchase_type = variant_elem.get("data-purchasetype", purchase_type)

            # Build form data
            form_data = {
                "clearCart": "0",
                "sylius_add_to_cart[cartItem][variant][purchaseType]": purchase_type,
                "sylius_add_to_cart[cartItem][variant][packaging]": packaging,
                "sylius_add_to_cart[cartItem][quantity]": str(item.quantity),
                "sylius_add_to_cart[_token]": csrf_token,
            }

            # Submit the form
            # The action is relative, so we need to construct the full URL
            submit_url = f"{self.BASE_URL}{action}" if action.startswith("/") else action

            try:
                response = self.session.post(
                    submit_url,
                    data=form_data,
                    timeout=self.timeout,
                    headers={
                        "X-Requested-With": "XMLHttpRequest",  # AJAX request
                        "Referer": product_url,
                    },
                )
                response.raise_for_status()
                print(f"Added {item.quantity}x {slug} ({packaging}) to cart")
            except Exception as e:
                print(f"Error adding {slug} to cart: {e}")

        return f"{self.BASE_URL}/en/cart/"

    def authenticate(self) -> None:
        """
        Authenticate with DoubleShot website.

        Uses username and password from instance variables (self.username, self.password).
        """
        if not self.username or not self.password:
            return

        try:
            # Get the login page to extract CSRF token
            login_url = f"{self.BASE_URL}/en/login"
            response = self.session.get(login_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Find CSRF token
            csrf_input = soup.select_one('input[name="_csrf_shop_security_token"]')
            if not csrf_input:
                print("Warning: Could not find CSRF token for login")
                return

            csrf_token = csrf_input.get("value", "")

            # Prepare login data
            login_data = {
                "_username": self.username,
                "_password": self.password,
                "_csrf_shop_security_token": csrf_token,
            }

            # Submit login form
            login_check_url = f"{self.BASE_URL}/en/login-check"
            response = self.session.post(
                login_check_url,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()

            # Check if login was successful
            # If successful, we should be redirected away from login page
            if "/login" in response.url:
                print("Warning: Login may have failed (still on login page)")
            else:
                print(f"Successfully authenticated as {self.username}")

        except Exception as e:
            print(f"Authentication error: {e}")

    def get_cart_url(self) -> str:
        """
        Get the cart URL for DoubleShot.

        Returns:
            Cart URL
        """
        return f"{self.BASE_URL}/en/cart/"

    def close(self):
        """Close HTTP session."""
        self.session.close()

    def _get_product_details(self, slug: str) -> Product | None:
        """
        Get detailed product information from product page.

        Args:
            slug: Product slug (e.g., 'start-espresso')

        Returns:
            Product object or None if parsing fails
        """
        try:
            url = f"{self.BASE_URL}/en/products/{slug}"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Get product name
            name_elem = soup.select_one("h1.productDetail-name, .productDetail-name")
            if not name_elem:
                # Try to get from title attribute or page title
                name = soup.select_one("title")
                name = name.text.split("|")[0].strip() if name else slug.replace("-", " ").title()
            else:
                name = name_elem.text.strip()

            # Get product ID from form action
            form = soup.select_one('form[name="sylius_add_to_cart"]')
            product_id = slug  # Default to slug

            if form:
                action = form.get("action", "")
                if "productId=" in action:
                    product_id = action.split("productId=")[1].split("&")[0]

            # Get variants and prices
            variants_div = soup.select_one("#sylius-variants-pricing")
            variants = []

            if variants_div:
                variant_elems = variants_div.select("[data-variant]")
                for variant_elem in variant_elems:
                    variant_id = variant_elem.get("data-variant", "")
                    packaging = variant_elem.get("data-packaging", "")
                    price_text = variant_elem.get("data-value", "0 Kč")
                    purchase_type = variant_elem.get("data-purchasetype", "one-time")

                    # Skip subscription variants for now
                    if purchase_type == "subscription":
                        continue

                    # Parse price
                    price_str = (
                        price_text.replace("Kč", "").replace(" ", "").replace("\xa0", "").strip()
                    )
                    try:
                        price = Decimal(price_str)
                    except (ValueError, ArithmeticError):
                        price = Decimal("0")

                    if price > 0:
                        # Create variant with price
                        variant = Variant(
                            id=variant_id,
                            name=packaging,
                            price=price,
                            attributes={
                                "packaging": packaging,
                                "purchase_type": purchase_type,
                            },
                        )
                        variants.append(variant)

            # Check availability
            available = len(variants) > 0

            # Create product
            return Product(
                id=product_id,
                name=name,
                roaster="doubleshot",
                available=available,
                url=url,
                variants=variants,
            )

        except Exception as e:
            print(f"Error parsing product {slug}: {e}")
            return None
