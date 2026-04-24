#!/usr/bin/env python3
"""
Aggregate orders and create shopping list with detailed markdown tables.

This script:
1. Reads orders from orders.json
2. Fetches product details from roaster
3. Creates polars DataFrames
4. Generates shopping list and aggregates
5. Outputs markdown tables with summaries
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

import polars as pl

from coffee_ordering.roasters import get_roaster_client


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate shopping list and aggregates")
    parser.add_argument(
        "--date",
        type=str,
        default=str(date.today()),
        help="Order date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--roaster",
        type=str,
        default="dosmundos",
        help="Roaster name",
    )
    args = parser.parse_args()

    # Set up paths
    orders_dir = Path(f"orders/{args.date}")
    if not orders_dir.exists():
        print(f"Error: Directory {orders_dir} does not exist")
        return

    # Read orders
    orders_file = orders_dir / "orders.json"
    if not orders_file.exists():
        print(f"Error: {orders_file} does not exist")
        return

    with open(orders_file) as f:
        orders = json.load(f)

    if not orders:
        print("No orders found")
        return

    print(f"📋 Processing {len(orders)} orders...")

    # Fetch product details
    print(f"📦 Fetching products from {args.roaster}...")
    roaster_class = get_roaster_client(args.roaster)
    with roaster_class(headless=True) as client:
        products = client.get_products()

    print(f"✓ Got {len(products)} products")

    # Create DataFrames
    orders_df = create_orders_dataframe(orders)
    products_df = create_products_dataframe(products)

    # Join orders with products
    shopping_df = join_orders_with_products(orders_df, products_df)

    # Generate outputs
    shopping_list_txt = generate_shopping_list_txt(shopping_df)
    markdown_output = generate_markdown_tables(shopping_df, args.date, args.roaster)

    # Save outputs
    shopping_list_file = orders_dir / "shopping_list.txt"
    shopping_list_file.write_text(shopping_list_txt)
    print(f"✓ Saved shopping list to {shopping_list_file}")

    markdown_file = orders_dir / "shopping_summary.md"
    markdown_file.write_text(markdown_output)
    print(f"✓ Saved markdown summary to {markdown_file}")

    # Also print to stdout for piping
    print("\n" + markdown_output)


def create_orders_dataframe(orders: list[dict]) -> pl.DataFrame:
    """Create polars DataFrame from orders."""
    return pl.DataFrame(orders)


def create_products_dataframe(products: list) -> pl.DataFrame:
    """Create polars DataFrame from products with flattened variants."""
    rows = []
    for product in products:
        for variant in product.variants:
            # Extract weight from variant name
            weight_kg = extract_weight_kg(variant.name)

            rows.append({
                "product_id": product.id,
                "product_name": product.name,
                "variant_id": variant.id,
                "variant_name": variant.name,
                "price": float(variant.price),
                "weight_kg": weight_kg,
            })

    return pl.DataFrame(rows)


def extract_weight_kg(variant_name: str) -> float:
    """Extract weight in kg from variant name."""
    # Match patterns like "250 g", "1 kg", "1000g"
    match = re.search(r"(\d+)\s*(g|kg)", variant_name.lower())
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == "g":
            return value / 1000
        else:
            return value
    return 0.0


def join_orders_with_products(orders_df: pl.DataFrame, products_df: pl.DataFrame) -> pl.DataFrame:
    """Join orders with product details."""
    # Join on both product_id and variant_id
    joined = orders_df.join(
        products_df,
        on=["product_id", "variant_id"],
        how="left"
    )

    # Calculate totals
    joined = joined.with_columns([
        (pl.col("quantity") * pl.col("price")).alias("total_price"),
        (pl.col("quantity") * pl.col("weight_kg")).alias("total_weight_kg"),
    ])

    return joined


def generate_shopping_list_txt(shopping_df: pl.DataFrame) -> str:
    """Generate simple text shopping list (product_id|variant_id|quantity)."""
    # Aggregate by product and variant
    aggregated = shopping_df.group_by(["product_id", "variant_id"]).agg([
        pl.col("quantity").sum()
    ]).sort("product_id")

    lines = []
    for row in aggregated.iter_rows(named=True):
        lines.append(f"{row['product_id']}|{row['variant_id']}|{row['quantity']}")

    return "\n".join(lines)


def generate_markdown_tables(shopping_df: pl.DataFrame, order_date: str, roaster: str) -> str:
    """Generate markdown with shopping list and per-person aggregates."""
    lines = []

    # Header
    lines.append(f"# Coffee Order Summary - {order_date}")
    lines.append(f"**Roaster:** {roaster.title()}")
    lines.append("")

    # Full shopping list table
    lines.append("## Full Shopping List")
    lines.append("")
    lines.extend(generate_shopping_list_table(shopping_df))
    lines.append("")

    # Individual bags table
    lines.append("## Individual Bags")
    lines.append("")
    lines.extend(generate_individual_bags_table(shopping_df))
    lines.append("")

    # Per-person aggregates
    lines.append("## Per-Person Aggregates")
    lines.append("")
    lines.extend(generate_person_aggregates_table(shopping_df))
    lines.append("")

    return "\n".join(lines)


def generate_shopping_list_table(shopping_df: pl.DataFrame) -> list[str]:
    """Generate shopping list markdown table with summary."""
    # Aggregate by product and variant
    aggregated = shopping_df.group_by(["product_id", "product_name", "variant_id", "variant_name", "price", "weight_kg"]).agg([
        pl.col("quantity").sum(),
    ]).with_columns([
        (pl.col("quantity") * pl.col("price")).alias("total_price"),
        (pl.col("quantity") * pl.col("weight_kg")).alias("total_weight_kg"),
    ]).sort("product_name", "variant_name")

    # Select and rename columns for display (keep types consistent)
    display_df = aggregated.select([
        pl.col("product_name").alias("Product"),
        pl.col("variant_name").alias("Variant"),
        pl.col("quantity").cast(pl.String).alias("Qty"),
        (pl.col("price").round(2).cast(pl.String) + " Kč").alias("Unit Price"),
        ("**" + pl.col("total_price").round(2).cast(pl.String) + " Kč**").alias("Total Price"),
        (pl.col("total_weight_kg").round(2).cast(pl.String) + " kg").alias("Weight"),
    ])

    # Calculate summary row
    total_bags = aggregated.select(pl.col("quantity").sum()).item()
    total_price = aggregated.select(pl.col("total_price").sum()).item()
    total_weight = aggregated.select(pl.col("total_weight_kg").sum()).item()

    # Create summary DataFrame (all strings to match display_df)
    summary_df = pl.DataFrame({
        "Product": ["**TOTAL**"],
        "Variant": [""],
        "Qty": [f"**{total_bags}**"],
        "Unit Price": [""],
        "Total Price": [f"**{total_price:.2f} Kč**"],
        "Weight": [f"**{total_weight:.2f} kg**"],
    })

    # Concatenate data and summary
    full_df = pl.concat([display_df, summary_df])

    # Generate markdown using Polars
    with pl.Config() as cfg:
        cfg.set_tbl_formatting('ASCII_MARKDOWN')
        cfg.set_tbl_hide_dataframe_shape(True)
        cfg.set_tbl_hide_column_data_types(True)
        cfg.set_tbl_rows(-1)  # Show all rows, don't truncate
        cfg.set_fmt_str_lengths(100)  # Don't truncate long strings
        markdown = repr(full_df)

    # Split into lines and return
    return markdown.strip().split('\n')


def generate_individual_bags_table(shopping_df: pl.DataFrame) -> list[str]:
    """Generate individual bags table with all details."""
    # Sort by person, then product for better readability
    sorted_df = shopping_df.sort("person", "product_name", "variant_name")

    # Expand rows - if quantity > 1, create multiple rows
    expanded_rows = []
    for row_dict in sorted_df.iter_rows(named=True):
        for i in range(row_dict['quantity']):
            expanded_rows.append({
                'person': row_dict['person'],
                'product_name': row_dict['product_name'],
                'variant_name': row_dict['variant_name'],
                'price': row_dict['price'],
                'weight_kg': row_dict['weight_kg'],
            })

    # Create DataFrame from expanded rows
    expanded_df = pl.DataFrame(expanded_rows)

    # Add bag number per person
    expanded_df = expanded_df.with_columns([
        pl.col("person").cum_count().over("person").alias("bag_num")
    ])

    # Select and format columns for display
    display_df = expanded_df.select([
        pl.col("person").alias("Person"),
        pl.col("bag_num").cast(pl.String).alias("#"),
        pl.col("product_name").alias("Product"),
        pl.col("variant_name").alias("Variant"),
        (pl.col("weight_kg").round(2).cast(pl.String) + " kg").alias("Weight"),
        (pl.col("price").round(2).cast(pl.String) + " Kč").alias("Price"),
    ])

    # Calculate summary row
    total_bags = len(expanded_df)
    total_weight = expanded_df.select(pl.col("weight_kg").sum()).item()
    total_price = expanded_df.select(pl.col("price").sum()).item()

    # Create summary DataFrame
    summary_df = pl.DataFrame({
        "Person": ["**TOTAL**"],
        "#": [f"**{total_bags}**"],
        "Product": [""],
        "Variant": [""],
        "Weight": [f"**{total_weight:.2f} kg**"],
        "Price": [f"**{total_price:.2f} Kč**"],
    })

    # Concatenate data and summary
    full_df = pl.concat([display_df, summary_df])

    # Generate markdown using Polars
    with pl.Config() as cfg:
        cfg.set_tbl_formatting('ASCII_MARKDOWN')
        cfg.set_tbl_hide_dataframe_shape(True)
        cfg.set_tbl_hide_column_data_types(True)
        cfg.set_tbl_rows(-1)  # Show all rows, don't truncate
        cfg.set_fmt_str_lengths(100)  # Don't truncate long strings
        markdown = repr(full_df)

    # Split into lines and return
    return markdown.strip().split('\n')


def generate_person_aggregates_table(shopping_df: pl.DataFrame) -> list[str]:
    """Generate per-person aggregates table with summary."""
    # Aggregate by person
    person_agg = shopping_df.group_by("person").agg([
        pl.col("quantity").sum().alias("num_bags"),
        pl.col("total_weight_kg").sum().alias("total_weight_kg"),
        pl.col("total_price").sum().alias("total_price"),
    ]).sort("person")

    # Select and rename columns for display (keep types consistent)
    display_df = person_agg.select([
        pl.col("person").alias("Person"),
        pl.col("num_bags").cast(pl.String).alias("Bags"),
        (pl.col("total_weight_kg").round(2).cast(pl.String) + " kg").alias("Total Weight"),
        ("**" + pl.col("total_price").round(2).cast(pl.String) + " Kč**").alias("Total Price"),
    ])

    # Calculate summary row
    total_bags = person_agg.select(pl.col("num_bags").sum()).item()
    total_weight = person_agg.select(pl.col("total_weight_kg").sum()).item()
    total_price = person_agg.select(pl.col("total_price").sum()).item()

    # Create summary DataFrame (all strings to match display_df)
    summary_df = pl.DataFrame({
        "Person": ["**TOTAL**"],
        "Bags": [f"**{total_bags}**"],
        "Total Weight": [f"**{total_weight:.2f} kg**"],
        "Total Price": [f"**{total_price:.2f} Kč**"],
    })

    # Concatenate data and summary
    full_df = pl.concat([display_df, summary_df])

    # Generate markdown using Polars
    with pl.Config() as cfg:
        cfg.set_tbl_formatting('ASCII_MARKDOWN')
        cfg.set_tbl_hide_dataframe_shape(True)
        cfg.set_tbl_hide_column_data_types(True)
        cfg.set_tbl_rows(-1)  # Show all rows, don't truncate
        cfg.set_fmt_str_lengths(100)  # Don't truncate long strings
        markdown = repr(full_df)

    # Split into lines and return
    return markdown.strip().split('\n')


if __name__ == '__main__':
    main()
