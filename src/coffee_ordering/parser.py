"""Shopping list parser for structured format."""

from pathlib import Path

from coffee_ordering.models import ShoppingListItem


class ShoppingListParser:
    """Parse structured shopping lists (product_id|variant_id|quantity format)."""

    def parse(self, text: str) -> list[ShoppingListItem]:
        """
        Parse shopping list text into structured items.

        Args:
            text: Raw shopping list text

        Returns:
            List of shopping list items
        """
        items = []
        lines = text.strip().split("\n")

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                # Skip empty lines and comments
                continue

            item = self._parse_line(line)
            if item:
                items.append(item)

        return items

    def _parse_line(self, line: str) -> ShoppingListItem:
        """
        Parse a single line in structured format.

        Format: product_id|variant_id|quantity or product_id|variant_id

        Args:
            line: Single line from shopping list

        Returns:
            ShoppingListItem

        Raises:
            ValueError: If line is not in correct format
        """
        # Check for structured format with pipe separator
        if "|" not in line:
            raise ValueError(
                f"Invalid format. Expected 'product_id|variant_id|quantity' or 'product_id|variant_id', got: {line}"
            )

        parts = line.split("|")

        if len(parts) < 2:
            raise ValueError(
                f"Invalid format. Need at least product_id and variant_id, got: {line}"
            )

        product_id = parts[0].strip()
        variant_id = parts[1].strip()
        quantity = 1

        # Validate product_id and variant_id are not empty
        if not product_id:
            raise ValueError(f"product_id cannot be empty in line: {line}")
        if not variant_id:
            raise ValueError(f"variant_id cannot be empty in line: {line}")

        # Parse quantity if provided
        if len(parts) >= 3:
            try:
                quantity = int(parts[2].strip())
                if quantity <= 0:
                    raise ValueError(f"quantity must be positive, got: {quantity} in line: {line}")
            except ValueError as e:
                if "positive" in str(e) or "empty" in str(e):
                    raise
                raise ValueError(f"quantity must be a number, got: {parts[2].strip()} in line: {line}")

        return ShoppingListItem(
            raw_text=line,
            product_name=product_id,
            quantity=quantity,
            preferences={
                "product_id": product_id,
                "variant_id": variant_id,
            }
        )

    def parse_file(self, filepath: str) -> list[ShoppingListItem]:
        """
        Parse shopping list from a file.

        Args:
            filepath: Path to shopping list file

        Returns:
            List of shopping list items
        """
        with Path(filepath).open(encoding="utf-8") as f:
            text = f.read()
        return self.parse(text)
