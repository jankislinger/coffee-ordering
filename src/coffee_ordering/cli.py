"""Command-line interface for coffee ordering."""

from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from coffee_ordering import __version__
from coffee_ordering.cart import CartManager
from coffee_ordering.config import settings
from coffee_ordering.models import CartItem
from coffee_ordering.parser import ShoppingListParser
from coffee_ordering.roasters import get_roaster_client


console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Coffee ordering automation tool."""


@main.command()
@click.option("--list", "list_file", type=click.Path(exists=True), help="Shopping list file")
@click.option("--items", multiple=True, help="Shopping list items (can be used multiple times)")
@click.option("--roaster", default=None, help="Roaster name (default: from config)")
def add_to_cart(
    list_file: Optional[str],
    items: tuple[str, ...],
    roaster: Optional[str],
) -> None:
    """Add items from shopping list to cart."""

    console.print(f"[bold cyan]☕ Coffee Ordering Tool v{__version__}[/bold cyan]\n")

    # Parse shopping list
    parser = ShoppingListParser()

    if list_file:
        console.print(f"📄 Reading shopping list from: {list_file}")
        shopping_items = parser.parse_file(list_file)
    elif items:
        console.print(f"📝 Processing {len(items)} items from command line")
        shopping_items = parser.parse("\n".join(items))
    else:
        console.print("[red]❌ No shopping list provided. Use --list or --items[/red]")
        return

    if not shopping_items:
        console.print("[yellow]⚠ No items found in shopping list[/yellow]")
        return

    console.print(f"✓ Parsed {len(shopping_items)} items\n")

    # Get roaster client
    roaster_name = roaster or settings.roaster
    console.print(f"🏪 Using roaster: {roaster_name}")

    try:
        roaster_class = get_roaster_client(roaster_name)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return

    # Fetch products
    console.print("📦 Fetching product catalog...")

    with roaster_class() as client:
        # Authenticate if credentials are available
        client.authenticate()

        products = client.get_products()

        if not products:
            console.print("[yellow]⚠ No products found. Implementation may be incomplete.[/yellow]")
            console.print("[yellow]  See docs/EXPLORATION_SUMMARY.md for next steps.[/yellow]")
            return

        console.print(f"✓ Found {len(products)} products\n")

        # Create product lookup map
        products_map = {p.id: p for p in products}

        # Convert shopping items to cart items
        console.print("🔍 Processing shopping list...")
        cart_items = []

        for item in shopping_items:
            product_id = item.preferences.get("product_id")
            variant_id = item.preferences.get("variant_id")

            # Find product
            product = products_map.get(product_id)
            if not product:
                console.print(f"[yellow]⚠ Product '{product_id}' not found[/yellow]")
                continue

            # Create cart item
            cart_item = CartItem(
                product_id=product_id,
                variant_id=variant_id,
                quantity=item.quantity,
            )
            cart_items.append(cart_item)
            console.print(f"  ✓ {item.quantity}x {product.name} (variant: {variant_id})")

        if not cart_items:
            console.print("[yellow]⚠ No valid items to add to cart[/yellow]")
            return

        # Add to cart
        if not click.confirm("\n🛒 Proceed with adding to cart?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        console.print("\n📤 Adding items to cart...")
        cart_url = client.add_to_cart(cart_items, products)

        console.print("\n[bold green]✅ Items added to cart![/bold green]")
        console.print(f"🛒 Cart URL: {cart_url}")
        console.print("\n💡 Visit the cart URL to complete your order manually")


@main.command()
@click.option("--roaster", default=None, help="Roaster name")
def list_cart(roaster: Optional[str]) -> None:
    """List current cart contents from the roaster website."""

    roaster_name = roaster or settings.roaster
    console.print(f"[bold cyan]🛒 Cart from {roaster_name}[/bold cyan]\n")

    try:
        roaster_class = get_roaster_client(roaster_name)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return

    with roaster_class() as client:
        # Authenticate if credentials available
        client.authenticate()

        # Get cart URL
        cart_url = client.get_cart_url()

        console.print(f"📍 Cart URL: {cart_url}\n")

        # TODO: Implement cart scraping in roaster clients
        # For now, just open the cart URL
        console.print("[yellow]💡 Cart listing not yet implemented.[/yellow]")
        console.print("[yellow]   Please visit the cart URL to see contents.[/yellow]")





@main.command()
@click.option("--roaster", default=None, help="Roaster name")
def list_products(roaster: Optional[str]) -> None:
    """List available products from a roaster."""

    roaster_name = roaster or settings.roaster
    console.print(f"[bold cyan]📦 Products from {roaster_name}[/bold cyan]\n")

    try:
        roaster_class = get_roaster_client(roaster_name)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return

    with roaster_class() as client:
        # Authenticate if credentials are available
        assert client.authenticate(), "Failed to authenticate"

        products = client.get_products()

        if not products:
            console.print("[yellow]⚠ No products found[/yellow]")
            return

        for product in products:
            # Print product header
            console.print(f"\n[bold cyan]Product ID:[/bold cyan] {product.id}")
            console.print(f"[bold]{product.name}[/bold]")
            console.print(f"Available: {'Yes' if product.available else 'No'}")

            # Print variants
            if product.variants:
                console.print("Variants:")
                for variant in product.variants:
                    console.print(f"  [ID: {variant.id}] {variant.name}: {variant.price} Kč")


if __name__ == "__main__":
    main()
