"""Roaster client implementations."""

from coffee_ordering.roasters.base import RoasterClient
from coffee_ordering.roasters.dosmundos import DosMundosClient
from coffee_ordering.roasters.doubleshot import DoubleShotClient


__all__ = [
    "DosMundosClient",
    "DoubleShotClient",
    "RoasterClient",
    "get_roaster_client",
    "ROASTERS",
]


# Roaster registry
ROASTERS = {
    "dosmundos": DosMundosClient,
    "doubleshot": DoubleShotClient,
}


def get_roaster_client(roaster_name: str) -> type[RoasterClient]:
    """
    Get roaster client class by name.

    Args:
        roaster_name: Name of the roaster (e.g., "dosmundos", "doubleshot")

    Returns:
        RoasterClient class

    Raises:
        ValueError: If roaster is not found

    Examples:
        >>> # Get DosMundos browser client
        >>> client_class = get_roaster_client("dosmundos")
        >>> client = client_class()

        >>> # Get DoubleShot client
        >>> client_class = get_roaster_client("doubleshot")
        >>> client = client_class()
    """
    if roaster_name not in ROASTERS:
        msg = f"Unknown roaster: {roaster_name}. Available roasters: {', '.join(ROASTERS.keys())}"
        raise ValueError(msg)

    return ROASTERS[roaster_name]
