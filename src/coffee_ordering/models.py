"""Data models for coffee ordering."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class Variant(BaseModel):
    """Product variant (size, grind type, etc.)."""

    id: str
    name: str
    price: Decimal
    attributes: dict[str, Any] = Field(default_factory=dict)


class Product(BaseModel):
    """Coffee product from a roaster."""

    id: str
    name: str
    roaster: str
    available: bool = True
    variants: list[Variant] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    url: str | None = None
    description: str | None = None


class ShoppingListItem(BaseModel):
    """Item from user's shopping list."""

    raw_text: str
    product_name: str | None = None
    quantity: int = 1
    preferences: dict[str, Any] = Field(default_factory=dict)


class CartItem(BaseModel):
    """Item in shopping cart."""

    product_id: str
    variant_id: str
    quantity: int = 1



