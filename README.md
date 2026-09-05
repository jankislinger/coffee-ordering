# Coffee Ordering Tool ☕

An automation tool that takes a structured coffee shopping list and adds the specified products to your cart at supported coffee roasters.

## Features

- 🛒 **Automated Cart Management**: Automatically adds specified products to the roaster's shopping cart
- 🔌 **Extensible Architecture**: Built to support multiple coffee roasters (currently supports doubleshot.cz and dos-mundos.cz)
- 💾 **Smart Caching**: Caches product catalogs to minimize scraping

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Account with supported roaster (optional, for cart management)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/coffee-ordering.git
cd coffee-ordering

# Install dependencies
pip install -e .

# Install Playwright browsers (required for Dos Mundos)
playwright install chromium
```

### Configuration

Create a `.env` file in the project root:

```env
ROASTER=doubleshot
DOUBLESHOT_USERNAME=your_username  # Optional
DOUBLESHOT_PASSWORD=your_password  # Optional
DOSMUNDOS_USERNAME=your_username   # Optional
DOSMUNDOS_PASSWORD=your_password   # Optional
```

### Usage

#### List Available Products

```bash
coffee-order list-products --roaster doubleshot
coffee-order list-products --roaster dosmundos
```

#### Add to Cart

Create a shopping list file `shopping-list.txt` using the structured format `product_id|variant_id|quantity`:

```
548|25011001_300|2
1100|032041502_1000|1
```

Run the tool (always prompts for confirmation before adding to cart):

```bash
coffee-order add-to-cart --list shopping-list.txt
```

#### Direct Input

```bash
coffee-order add-to-cart --items "548|25011001_300|2" --items "1100|032041502_1000|1"
```

## Example Workflow

1. **List available products** to find product and variant IDs:
   ```bash
   coffee-order list-products --roaster doubleshot
   ```

2. **Create your shopping list** in `product_id|variant_id|quantity` format:
   ```
   548|25011001_300|2
   1100|032041502_1000|1
   ```

3. **Run the tool** and confirm when prompted:
   ```bash
   coffee-order add-to-cart --list my-list.txt
   ```

4. **Complete checkout** by visiting the cart URL printed after items are added.

## Supported Roasters

- ✅ **doubleshot.cz** - Fully supported (requests-based)
- ✅ **dos-mundos.cz** - Fully supported (browser automation via Playwright)
- 🚧 More roasters coming soon!

### Selecting Clients Dynamically

Use `get_roaster_client()` to get a roaster client class by name:

```python
from coffee_ordering.roasters import get_roaster_client

ClientClass = get_roaster_client("dosmundos")
client = ClientClass()
```

### Dos Mundos Client

The Dos Mundos roastery uses Shoptet platform with bot detection. The client uses browser automation (Playwright):

```python
from coffee_ordering.roasters import DosMundosClient

with DosMundosClient(headless=True) as client:
    client.authenticate()
    products = client.get_products()
```

## Project Structure

```
coffee-ordering/
├── src/
│   └── coffee_ordering/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── parser.py           # Shopping list parser
│       ├── cart.py             # Cart management
│       ├── roasters/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract roaster client
│       │   ├── doubleshot.py   # DoubleShot implementation
│       │   └── dosmundos.py    # Dos Mundos implementation
│       ├── models.py           # Data models
│       └── config.py           # Configuration management
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── orders/                     # Per-round order data
├── README.md
└── pyproject.toml
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/coffee-ordering.git
cd coffee-ordering

# Install with development dependencies
uv sync
```

### Running Tests

The project uses pytest for testing:

```bash
uv run pytest
uv run pytest -v
uv run pytest tests/test_parser.py  # Run specific test file
```

### Code Quality

The project uses ruff for linting and formatting:

```bash
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uv run ruff check --fix src/ tests/
```

### Adding a New Roaster

1. Create a new file in `src/coffee_ordering/roasters/`
2. Inherit from `RoasterClient` base class
3. Implement required methods:
   - `get_products()`
   - `add_to_cart()`
   - `authenticate()`
   - `get_cart_url()`
   - `close()`
4. Register the new class in the `ROASTERS` dict in `src/coffee_ordering/roasters/__init__.py`

## Configuration Options

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| Roaster | `ROASTER` | Default roaster to use |
| DoubleShot Username | `DOUBLESHOT_USERNAME` | DoubleShot login email |
| DoubleShot Password | `DOUBLESHOT_PASSWORD` | DoubleShot password |
| Dos Mundos Username | `DOSMUNDOS_USERNAME` | Dos Mundos login email |
| Dos Mundos Password | `DOSMUNDOS_PASSWORD` | Dos Mundos password |

## Troubleshooting

### "No products found"
- Check your internet connection
- Verify the roaster's website is accessible

### "Authentication failed"
- Verify your credentials in `.env` file
- Check if the roaster's website is working
- Try logging in manually first

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License

## Roadmap

- [ ] Support for more roasters
- [ ] Price comparison across roasters
- [ ] Subscription/recurring order management
- [ ] Web UI
- [ ] Mobile app
- [ ] Local LLM support for privacy
- [ ] Order history tracking
- [ ] Price alerts

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: This tool is not affiliated with any coffee roaster. Always review your cart before completing checkout.
