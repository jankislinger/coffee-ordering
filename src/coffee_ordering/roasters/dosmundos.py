"""Dos Mundos roaster client implementation using browser automation."""

import json
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from coffee_ordering.models import CartItem, Product, Variant
from coffee_ordering.roasters.base import RoasterClient


class DosMundosClient(RoasterClient):
    """Client for dos-mundos.cz roaster (Shoptet platform) using browser automation."""

    BASE_URL = "https://www.dos-mundos.cz"

    def __init__(self, username: str = "", password: str = "", headless: bool = False, **kwargs):
        """
        Initialize Dos Mundos browser client.

        Args:
            username: Optional username for authentication (defaults to DOSMUNDOS_USERNAME env var)
            password: Optional password for authentication (defaults to DOSMUNDOS_PASSWORD env var)
            headless: Whether to run browser in headless mode (default: True)
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        # Use provided credentials or fall back to environment variables
        self.username = username or os.getenv("DOSMUNDOS_USERNAME", "")
        self.password = password or os.getenv("DOSMUNDOS_PASSWORD", "")
        self.headless = headless
        self.timeout = 30000  # 30 seconds in milliseconds for Playwright

        # Browser components (initialized on first use)
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        """Get or create browser page."""
        if self._page is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            self._context.set_default_timeout(self.timeout)
            self._page = self._context.new_page()
        return self._page

    def _get_cache_path(self) -> Path:
        """Get cache file path for products."""
        cache_dir = Path.cwd() / ".cache" / "dosmundos"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "products.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is less than 24 hours old."""
        if not cache_path.exists():
            return False

        # Get file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime

        # Cache is valid if less than 24 hours old
        return age < timedelta(hours=24)

    def _load_cache(self, cache_path: Path) -> list[Product]:
        """Load products from cache file."""
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert JSON back to Product objects
        products = []
        for p_data in data:
            # Convert float prices back to Decimal
            variants = []
            for v_data in p_data.get('variants', []):
                v_data['price'] = Decimal(str(v_data['price']))  # float -> Decimal
                variants.append(Variant(**v_data))

            product = Product(
                id=p_data['id'],
                name=p_data['name'],
                roaster=p_data['roaster'],
                available=p_data['available'],
                variants=variants
            )
            products.append(product)

        return products

    def _save_cache(self, cache_path: Path, products: list[Product]) -> None:
        """Save products to cache file."""
        # Convert Product objects to JSON-serializable dicts
        data = []
        for p in products:
            # Convert Decimal prices to float for JSON serialization
            variants_data = []
            for v in p.variants:
                v_dict = v.model_dump()
                v_dict['price'] = float(v_dict['price'])  # Decimal -> float
                variants_data.append(v_dict)

            data.append({
                'id': p.id,
                'name': p.name,
                'roaster': p.roaster,
                'available': p.available,
                'variants': variants_data
            })

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_products(self) -> list[Product]:
        """
        Fetch all available products from Dos Mundos.

        This method uses a cache to avoid unnecessary scraping.
        Cache is stored in .cache/dosmundos/products.json and is
        valid for 24 hours.

        Returns:
            List of products
        """
        # Check cache first
        cache_path = self._get_cache_path()
        if self._is_cache_valid(cache_path):
            print("✓ Using cached products (less than 24 hours old)")
            return self._load_cache(cache_path)

        print("⟳ Cache expired or missing, fetching fresh products...")
        products = []

        # Fetch the coffee-only category page (Czech: "Jednodruhová káva 100% arabica")
        # This category contains only coffee products, filtering out equipment and accessories
        base_url = f"{self.BASE_URL}/jednodruhova-kava-100--arabica/"

        # Fetch all pages (Shoptet uses pagination)
        page_num = 1
        while True:
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}strana-{page_num}/"

            try:
                self.page.goto(url, wait_until="domcontentloaded")
                # Wait a bit for dynamic content
                self.page.wait_for_timeout(1000)
            except Exception:
                # If we can't load the page, we've likely reached the end
                break

            html = self.page.content()
            soup = BeautifulSoup(html, "lxml")

            # Find all product items
            product_items = soup.select(".product")

            # If no products found, we've reached the end
            if not product_items:
                break

            for item in product_items:
                # Get product link
                link = item.select_one("a.name")
                if not link:
                    continue

                href = link.get("href", "")
                if not href:
                    continue

                # Get product details from the product page
                product = self._get_product_details(href)
                if product:
                    products.append(product)

            # Check if there's a next page
            next_page = soup.select_one(f'a[href*="strana-{page_num + 1}"]')
            if not next_page:
                break

            page_num += 1

        # Save to cache
        self._save_cache(cache_path, products)
        print(f"✓ Cached {len(products)} products")

        return products

    def add_to_cart(self, items: list[CartItem], products: list[Product]) -> str:
        """
        Add items to the Dos Mundos shopping cart.

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

            # Navigate to product page
            product_url = product.url or f"{self.BASE_URL}/{product.id}"

            try:
                self.page.goto(product_url, wait_until="domcontentloaded")
                self.page.wait_for_timeout(500)

                # Select variant if specified
                if item.variant_id and item.variant_id != "default":
                    # Extract parameter_id from variant attributes
                    param_id = None
                    for variant in product.variants:
                        if variant.id == item.variant_id:
                            param_id = variant.attributes.get("parameter_id")
                            break

                    if param_id:
                        # Select the variant from dropdown
                        select_id = f"#parameter-id-{param_id}"
                        if self.page.locator(select_id).count() > 0:
                            self.page.select_option(select_id, item.variant_id)
                            # Wait for price update
                            self.page.wait_for_timeout(500)

                # Set quantity (use data-testid to target the visible input)
                quantity_input = self.page.get_by_test_id('cartAmount')
                if quantity_input.count() > 0:
                    # Clear and fill the quantity field
                    quantity_input.click()  # Focus the input
                    quantity_input.fill("")  # Clear first
                    quantity_input.fill(str(item.quantity))  # Then fill
                    # Wait for any JavaScript events to complete
                    self.page.wait_for_timeout(500)
                else:
                    print(f"Warning: Could not find quantity input for {product.name}")

                # Click add to cart button - use .first to get the main product button
                # (page has multiple buttons for related products)
                add_to_cart_btn = self.page.get_by_test_id('buttonAddToCart').first
                if add_to_cart_btn.count() > 0:
                    add_to_cart_btn.click()
                    # Wait for cart update and any notifications
                    self.page.wait_for_timeout(1500)
                    print(f"✓ Added {item.quantity}x {product.name} to cart")
                else:
                    print(f"✗ Warning: Could not find add to cart button for {product.name}")

            except Exception as e:
                print(f"✗ Error adding {product.name} to cart: {e}")
                # Continue with next item instead of failing completely

        return f"{self.BASE_URL}/kosik/"

    def authenticate(self) -> None:
        """
        Authenticate with Dos Mundos website.

        Uses username and password from instance variables (self.username, self.password).
        This implementation uses browser automation to bypass bot detection.
        """
        if not self.username or not self.password:
            return

        try:
            # Navigate to login page
            login_url = f"{self.BASE_URL}"
            self.page.goto(login_url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

            # Note: The /prihlaseni/ page has the login form elements but they are hidden
            # This appears to be a Shoptet e-shop behavior where the form exists in the DOM
            # but is not visible/interactable via Playwright force=True
            #
            # Workaround: Use JavaScript to directly submit the form
            print("Note: Login form is hidden on page, attempting JavaScript submission...")

            try:
                # Use JavaScript to fill and submit the form directly
                self.page.evaluate("""
                    (credentials) => {
                        const emailInput = document.querySelector('[data-testid="inputEmail"]');
                        const passwordInput = document.querySelector('input[name="password"][type="password"]');
                        const surnameInput = document.querySelector('[data-testid="formLogin"] input[name="surname"]');
                        const form = document.querySelector('[data-testid="formLogin"]');

                        if (emailInput && passwordInput && form) {
                            emailInput.value = credentials.username;
                            passwordInput.value = credentials.password;
                            if (surnameInput) surnameInput.value = '';  // Honeypot
                            form.submit();
                            return true;
                        }
                        return false;
                    }
                """, {"username": self.username, "password": self.password})

                print("Form submitted via JavaScript")

                # Wait for navigation after form submission
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_timeout(2000)

                # Check if login was successful
                current_url = self.page.url
                if "/prihlaseni/" in current_url:
                    print("Warning: Login may have failed (still on login page)")
                else:
                    print(f"✓ Successfully authenticated as {self.username}")

            except Exception as e:
                print(f"Warning: JavaScript form submission failed: {e}")
                print("Login may not work - continuing anyway")

        except Exception as e:
            print(f"Authentication error: {e}")

    def get_cart_url(self) -> str:
        """
        Get the cart URL for Dos Mundos.

        Returns:
            Cart URL
        """
        return f"{self.BASE_URL}/kosik/"

    def close(self):
        """Close browser and cleanup resources."""
        if self._page:
            self._page.close()
            self._page = None
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _extract_csrf_token(self, soup: BeautifulSoup) -> str:
        """
        Extract CSRF token from Shoptet page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            CSRF token string or empty string if not found
        """
        # Try to find token in script tags
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "shoptet.csrf.token" in script.string:
                match = re.search(r'shoptet\.csrf\.token\s*=\s*["\']([^"\']+)["\']', script.string)
                if match:
                    return match.group(1)
        return ""

    def _get_product_details(self, url: str) -> Product | None:
        """
        Get detailed product information from product page.

        Args:
            url: Product URL (can be relative or absolute)

        Returns:
            Product object or None if parsing fails
        """
        try:
            # Make URL absolute if needed
            if not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

            html = self.page.content()
            soup = BeautifulSoup(html, "lxml")

            # Get product name
            name_elem = soup.select_one("h1")
            if not name_elem:
                return None
            name = name_elem.text.strip()

            # Extract product code/ID from URL
            product_id = url.rstrip("/").split("/")[-1]

            # Get variants and prices
            variants = []

            # Look for parameter selects (Shoptet uses parameter-based variants)
            param_selects = soup.select("select[id^='parameter-id-']")

            if param_selects:
                # Get the first parameter select (usually package size)
                variant_select = param_selects[0]
                param_id = variant_select.get("id", "").replace("parameter-id-", "")

                options = variant_select.select("option")
                for option in options:
                    variant_id = option.get("value", "")
                    if not variant_id or variant_id == "":
                        continue

                    option_text = option.text.strip()

                    # Look for corresponding price element
                    # Use attribute selector since class names can start with numbers
                    price_holders = soup.select(".price-final-holder.parameter-dependent")
                    price_elem = None
                    for holder in price_holders:
                        classes = holder.get("class", [])
                        target_class = f"{param_id}-{variant_id}"
                        if target_class in classes:
                            price_elem = holder
                            break

                    if price_elem:
                        price_text = price_elem.text.strip()
                        price_match = re.search(r"(\d+(?:\s?\d+)*(?:[.,]\d+)?)\s*Kč", price_text)
                        if price_match:
                            price_str = price_match.group(1).replace(" ", "").replace(",", ".")
                            try:
                                price = Decimal(price_str)
                            except (ValueError, ArithmeticError):
                                price = Decimal("0")
                        else:
                            price = Decimal("0")
                    else:
                        price = Decimal("0")

                    if price > 0:
                        variant = Variant(
                            id=variant_id,
                            name=option_text,
                            price=price,
                            attributes={
                                "packaging": option_text,
                                "parameter_id": param_id,
                            },
                        )
                        variants.append(variant)

            # If no variants found, try to get base price and create a default variant
            if not variants:
                price_elem = soup.select_one(".price-final, .p-final-price")
                if price_elem:
                    price_text = price_elem.text.strip()
                    price_match = re.search(r"(\d+(?:\s?\d+)*(?:[.,]\d+)?)", price_text)
                    if price_match:
                        price_str = price_match.group(1).replace(" ", "").replace(",", ".")
                        try:
                            price = Decimal(price_str)
                            # Create a default variant with the base price
                            variant = Variant(
                                id="default",
                                name="Standard",
                                price=price,
                                attributes={},
                            )
                            variants.append(variant)
                        except (ValueError, ArithmeticError):
                            pass

            # Check availability
            available = len(variants) > 0

            # Create product
            return Product(
                id=product_id,
                name=name,
                roaster="dosmundos",
                available=available,
                url=url,
                variants=variants,
            )

        except Exception as e:
            print(f"Error parsing product {url}: {e}")
            return None
