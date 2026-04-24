# Coffee Ordering Tool ☕

An intelligent automation tool that takes your unstructured coffee shopping list and automatically orders from your favorite coffee roasters. Using LLM-powered product matching, it maps your casual descriptions to actual products and adds them to your cart.

## Features

- 📝 **Natural Language Shopping Lists**: Write your shopping list in plain text, no structured format needed
- 🤖 **AI-Powered Matching**: Uses LLMs to intelligently match your items to actual products
- 🛒 **Automated Cart Management**: Automatically adds matched products to the roaster's shopping cart
- 🔌 **Extensible Architecture**: Built to support multiple coffee roasters (currently supports doubleshot.cz)
- 💾 **Smart Caching**: Caches product catalogs to minimize API calls
- ✅ **Confidence Scoring**: Shows match confidence and allows review before ordering

## Quick Start

### Prerequisites

- Python 3.13 or higher
- API key for OpenAI or Anthropic (for LLM matching)
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
OPENAI_API_KEY=your_api_key_here
COFFEE_ROASTER=doubleshot
DOUBLESHOT_USERNAME=your_username  # Optional
DOUBLESHOT_PASSWORD=your_password  # Optional
```

Or use a configuration file `coffee-ordering.yaml`:

```yaml
roaster: doubleshot
llm:
  provider: openai
  model: gpt-4
  temperature: 0.1
cache:
  enabled: true
  ttl: 3600
```

### Usage

#### Basic Usage

Create a shopping list file `shopping-list.txt`:

```
2x Ethiopian Natural 250g
1 Colombian washed, whole beans
Kenya AA medium roast 500g
```

Run the tool:

```bash
coffee-order --list shopping-list.txt
```

#### Interactive Mode

```bash
coffee-order --interactive
```

#### Direct Input

```bash
coffee-order --items "Ethiopian 250g" "Colombian washed"
```

#### Review Before Adding to Cart

```bash
coffee-order --list shopping-list.txt --review
```

This will show you the matched products and ask for confirmation before adding to cart.

## Example Workflow

1. **Create your shopping list** (any format works):
   ```
   - 2 bags of that Ethiopian natural process
   - Colombian, washed, whole beans
   - Kenya AA if they have it, 500g
   ```

2. **Run the tool**:
   ```bash
   coffee-order --list my-list.txt --review
   ```

3. **Review the matches**:
   ```
   ✓ Matched: "Ethiopian natural process" → Ethiopia Guji Natural 250g ($18.50) [Confidence: 95%]
   ✓ Matched: "Colombian, washed, whole beans" → Colombia Huila Washed 250g ($16.00) [Confidence: 92%]
   ✓ Matched: "Kenya AA 500g" → Kenya Nyeri AA 500g ($32.00) [Confidence: 98%]

   Total: $67.00

   Proceed with adding to cart? [y/N]:
   ```

4. **Confirm and checkout**:
   ```
   ✓ Added 3 items to cart
   🛒 Cart URL: https://doubleshot.cz/cart
   ```

## Supported Roasters

- ✅ **doubleshot.cz** - Fully supported (requests-based)
- ✅ **dos-mundos.cz** - Fully supported (requests + browser automation)
  - Requests-based client: Fast scraping, no auth
  - Browser-based client: Full authentication support
- 🚧 More roasters coming soon!

### Selecting Clients Dynamically

Use `get_roaster_client()` to dynamically select between standard and browser-based clients:

```python
from coffee_ordering.roasters import get_roaster_client

# Fast standard client (for browsing)
ClientClass = get_roaster_client("dosmundos")
client = ClientClass()

# Browser client (for authentication)
ClientClass = get_roaster_client("dosmundos", use_browser=True)
client = ClientClass(headless=True)
client.authenticate()  # Actually works!
```

See [docs/GET_ROASTER_CLIENT.md](docs/GET_ROASTER_CLIENT.md) for details.

### Dos Mundos Browser Client

The Dos Mundos roastery uses Shoptet platform with bot detection. For authentication, use the browser-based client:

```python
from coffee_ordering.roasters import DosMundosBrowserClient

with DosMundosBrowserClient(headless=True) as client:
    client.authenticate()  # Actually works!
    products = client.get_products()
```

See [docs/DOS_MUNDOS_BROWSER_CLIENT.md](docs/DOS_MUNDOS_BROWSER_CLIENT.md) for more details.

## Project Structure

```
coffee-ordering/
├── src/
│   └── coffee_ordering/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── parser.py           # Shopping list parser
│       ├── matcher.py          # LLM-based product matcher
│       ├── cart.py             # Cart management
│       ├── roasters/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract roaster client
│       │   └── doubleshot.py   # DoubleShot implementation
│       ├── models.py           # Data models
│       ├── config.py           # Configuration management
│       └── py.typed            # Type checking marker
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
│   ├── DESIGN.md              # Architecture documentation
│   ├── API_FINDINGS.md        # API exploration results
│   └── EXPLORATION_SUMMARY.md # Exploration summary
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

The project uses pytest for testing. You can run tests in several ways:

```bash
# Run all tests
make test

# Run tests with verbose output
make test-v

# Run tests with coverage report (requires pytest-cov)
make test-cov

# Or use pytest directly
uv run pytest
uv run pytest -v
uv run pytest tests/test_parser.py  # Run specific test file
```

### Code Quality

The project uses ruff for linting and formatting:

```bash
# Format code
make format

# Run linter
make lint

# Fix linting issues automatically
make fix

# Run all checks (format + lint + test)
make all

# Or use ruff directly
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uv run ruff check --fix src/ tests/
```

### Available Make Commands

Run `make help` to see all available commands:

```bash
make help
```

### Adding a New Roaster

1. Create a new file in `src/coffee_ordering/roasters/`
2. Inherit from `RoasterClient` base class
3. Implement required methods:
   - `get_products()`
   - `add_to_cart()`
   - `authenticate()`
4. Register in the roaster registry

See `docs/DESIGN.md` for detailed architecture documentation.

## Configuration Options

| Option | Environment Variable | Config File | Description |
|--------|---------------------|-------------|-------------|
| Roaster | `COFFEE_ROASTER` | `roaster` | Default roaster to use |
| LLM Provider | `LLM_PROVIDER` | `llm.provider` | openai or anthropic |
| LLM Model | `LLM_MODEL` | `llm.model` | Model name (e.g., gpt-4) |
| API Key | `OPENAI_API_KEY` | - | LLM API key |
| Cache Enabled | `CACHE_ENABLED` | `cache.enabled` | Enable product caching |
| Cache TTL | `CACHE_TTL` | `cache.ttl` | Cache lifetime in seconds |

## Troubleshooting

### "No products found"
- Check your internet connection
- Verify the roaster's website is accessible
- Try clearing the cache: `coffee-order --clear-cache`

### "Low confidence matches"
- Be more specific in your shopping list
- Include product details like origin, process, size
- Use the `--review` flag to manually verify matches

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

MIT License - see LICENSE file for details

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
