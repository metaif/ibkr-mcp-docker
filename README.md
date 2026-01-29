# IBKR MCP Docker

[中文文档](README_CN.md) | English

A Model Context Protocol (MCP) server that provides Interactive Brokers (IBKR) trading capabilities through Docker.

---

## ⚠️ IMPORTANT DISCLAIMER

**THIS SOFTWARE IS PROVIDED FOR INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY. BY USING THIS SOFTWARE, YOU ACKNOWLEDGE AND AGREE THAT:**

- **YOU ARE SOLELY RESPONSIBLE** for all trading decisions and operations made through this software
- You use this software **AT YOUR OWN RISK**. The authors and contributors are not responsible for any financial losses, damages, or liabilities
- This software connects to your **real financial accounts**. Improper use may result in significant financial loss
- **ALWAYS** test with **Paper Trading** mode first before using with live accounts
- You should fully understand the risks of automated trading and the Interactive Brokers platform before use

**USE AT YOUR OWN RISK. NO WARRANTY OF ANY KIND.**

---

## What Does This Project Do?

This project provides a **bridge** between the Model Context Protocol (MCP) and Interactive Brokers trading platform. It allows AI assistants and applications to:

1. **Query real-time market data** - Get live stock prices, historical data, and option chains
2. **Monitor account status** - Check balances, positions, and portfolio performance
3. **Execute trades** - Place market orders, limit orders, and stop-loss orders programmatically
4. **Integrate with AI workflows** - Use natural language to interact with your brokerage account

## Features

This MCP server provides the following capabilities:

### Account Management
- Query account cash flow and balances
- View account summary and net liquidation value

### Position Management
- Query current positions
- View unrealized and realized P&L

### Order Management
- Query order status (open and filled orders)
- Place limit orders
- Place market orders
- Place stop-loss orders

### Market Data
- Get real-time stock prices *(requires market data subscription)*
- Query historical stock data
- Access option chains *(requires market data subscription)*

## Architecture

This project integrates two services:

1. **IB Gateway** - Uses [ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker) to provide the Interactive Brokers Gateway
2. **MCP Server** - A Python-based MCP server built with [FastMCP](https://github.com/jlowin/fastmcp) and [ib_async](https://ib-api-reloaded.github.io/ib_async/readme.html)

**Key Features:**
- **FastMCP Integration**: Uses decorator-based tool registration for clean, Pythonic code
- **Pydantic Models**: All responses are typed using Pydantic models for structured, validated data
- **Type Safety**: Full type hints and automatic schema generation from function signatures
- **HTTP/SSE Transport**: Exposes MCP server via HTTP at `http://127.0.0.1:8080/mcp`
- **Read-Only Mode**: Optional READONLY mode to disable order placement, modification, and cancellation

Both services are configured through a single `.env` file for simplicity.

## Prerequisites

- Docker and Docker Compose
- Interactive Brokers account (Paper Trading or Live)
- IBKR account credentials
- **Market data subscription** (required for real-time price data and options data)

> **Note**: Some features require an active IBKR market data subscription. Without a subscription, you may receive delayed data or no data for certain markets.

## Quick Start (Recommended: Use Pre-built Images)

**We recommend using pre-built Docker images** for easier setup and automatic updates. Pre-built images are:
- ✅ Tested and verified
- ✅ Multi-platform (amd64/arm64)
- ✅ Automatically built from releases
- ✅ No local build required

### Using Pre-built Images

1. Create a `.env` file from the example:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your IBKR credentials (see [Configuration](#configuration) section below)

3. Start the services:
```bash
docker-compose up -d
```

### Alternative: Build from Source

If you prefer to build from source:

1. Clone this repository:
```bash
git clone https://github.com/metaif/ibkr-mcp-docker.git
cd ibkr-mcp-docker
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit the `.env` file with your IBKR credentials:
```bash
# IBKR Gateway Configuration
IBKR_USERID=your_username
IBKR_PASSWORD=your_password
IBKR_TRADING_MODE=paper  # or 'live' for live trading
IBKR_GATEWAY_PORT=4002

# MCP Server Configuration
SERVER_PORT=8080  # MCP server will be available at http://127.0.0.1:8080/mcp

# Read-Only Mode (optional)
READONLY=false  # Set to 'true' to disable order operations

# Optional: VNC password for monitoring the gateway
VNC_PASSWORD=your_vnc_password
```

4. Update `docker-compose.yml` to build from source:

   Replace the image line with build configuration:

```yaml
services:
  mcp-server:
    build: .
    # Remove or comment out: image: ghcr.io/metaif/ibkr-mcp-docker:latest
```

5. Build and start the services:
```bash
docker-compose up -d --build
```

## Configuration

### Environment Variables

All configuration is done through the `.env` file. Here's a detailed explanation of each parameter:

#### IBKR Gateway Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `IBKR_TRADING_MODE` | Trading mode: `paper` for paper trading, `live` for live trading | `paper` | Yes |
| `IBKR_USERID` | IBKR username for live trading | - | Yes (for live) |
| `IBKR_PASSWORD` | IBKR password for live trading | - | Yes (for live) |
| `IBKR_USERID_PAPER` | IBKR username for paper trading | - | Yes (for paper) |
| `IBKR_PASSWORD_PAPER` | IBKR password for paper trading | - | Yes (for paper) |
| `IBKR_GATEWAY_LIVE_PORT` | IB Gateway port for live trading | `4003` | No |
| `IBKR_GATEWAY_PAPER_PORT` | IB Gateway port for paper trading | `4004` | No |
| `VNC_PASSWORD` | VNC password for monitoring the gateway UI | - | No |

#### MCP Server Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVER_PORT` | MCP server HTTP port. Server will be at `http://127.0.0.1:<PORT>/mcp` | `8080` | No |
| `READONLY` | Read-only mode. Set to `true`/`1`/`yes` to disable order operations | `false` | No |

### Configuration Example

Edit your `.env` file:

```bash
# For Paper Trading
IBKR_TRADING_MODE=paper
IBKR_USERID_PAPER=your_paper_username
IBKR_PASSWORD_PAPER=your_paper_password
IBKR_GATEWAY_PAPER_PORT=4004

# For Live Trading - BE CAREFUL!
# IBKR_TRADING_MODE=live
# IBKR_USERID=your_live_username
# IBKR_PASSWORD=your_live_password
# IBKR_GATEWAY_LIVE_PORT=4003

# MCP Server
SERVER_PORT=8080

# Safety: Enable read-only mode to prevent accidental trades
READONLY=true

# Optional: VNC for monitoring
VNC_PASSWORD=12345678
```

## Usage

### Starting the Services

Start both the IB Gateway and MCP server:

```bash
docker-compose up -d
```

This will:
- Start the IB Gateway container and connect to IBKR
- Start the MCP server container
- Expose the MCP server at `http://127.0.0.1:8080/mcp`

### Using the MCP Server

The MCP server is accessible via HTTP/SSE at:

```bash
# Access the MCP endpoint
curl http://localhost:8080/mcp
```

The endpoint is compatible with HTTP-based MCP clients and can be integrated into your applications.

### Monitoring

You can monitor the IB Gateway using VNC on port 5900:

```bash
# Using a VNC client, connect to:
localhost:5900
```

View logs:

```bash
# All services
docker-compose logs -f

# Just the MCP server
docker-compose logs -f mcp-server

# Just the IB Gateway
docker-compose logs -f ib-gateway
```

### Available MCP API Tools

The MCP server exposes the following tools. Each tool returns typed, validated responses using Pydantic models.

#### Account & Portfolio APIs

**These APIs do NOT require market data subscriptions:**

1. **`get_account_summary`** → `AccountSummary`
   - Get account balance and cash flow information
   - Returns: `net_liquidation`, `cash_balance`, `total_cash_value`, `buying_power`, `gross_position_value`
   - **No market data subscription required**

2. **`get_positions`** → `List[Position]`
   - Get all current positions
   - Each position includes: `symbol`, `quantity`, `avg_cost`, `market_price`, `unrealized_pnl`, `realized_pnl`
   - **No market data subscription required**

3. **`get_orders`** → `List[OrderInfo]`
   - Get all orders (open and filled)
   - Includes: `order_id`, `symbol`, `action`, `order_type`, `status`, `filled`, `avg_fill_price`
   - **No market data subscription required**

#### Market Data APIs

**These APIs REQUIRE market data subscriptions:**

4. **`get_stock_price`** → `StockPrice`
   - Get real-time stock price
   - Parameters: `symbol` (required), `exchange` (optional, default: "SMART")
   - Returns: `bid`, `ask`, `last`, `close`, `volume`, `timestamp`
   - **⚠️ REQUIRES market data subscription**
   - **Note**: Without subscription, may return delayed data or fail for certain markets

5. **`get_historical_data`** → `List[HistoricalBar]`
   - Get historical stock data
   - Parameters: `symbol` (required), `duration` (default: "1 D"), `bar_size` (default: "1 hour"), `exchange` (optional)
   - Returns: OHLCV data for each bar (`date`, `open`, `high`, `low`, `close`, `volume`)
   - **May require market data subscription depending on the data requested**

6. **`get_option_chain`** → `List[OptionChain]`
   - Get option chain for a stock
   - Parameters: `symbol` (required), `exchange` (optional)
   - Returns: Available `strikes`, `expirations`, `multipliers`
   - **⚠️ REQUIRES market data subscription for options**

#### Trading APIs

**These APIs do NOT require market data subscriptions but modify your account:**

7. **`place_limit_order`** → `OrderResult`
   - Place a limit order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `limit_price`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled**
   - **⚠️ CAUTION: This places real orders!**

8. **`place_market_order`** → `OrderResult`
   - Place a market order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled**
   - **⚠️ CAUTION: This places real orders!**

9. **`place_stop_order`** → `OrderResult`
   - Place a stop-loss order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `stop_price`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled**
   - **⚠️ CAUTION: This places real orders!**

10. **`cancel_order`** → `CancelResult`
    - Cancel an existing order
    - Parameters: `order_id` (required)
    - **⚠️ Disabled when READONLY mode is enabled**

All tools use **Pydantic models** for type-safe, validated responses with clear field descriptions.

### Read-Only Mode

Enable read-only mode to prevent order placement, modification, and cancellation:

```bash
READONLY=true
```

When enabled:
- ✅ All query operations (positions, orders, prices, etc.) work normally
- ❌ Order placement tools (`place_limit_order`, `place_market_order`, `place_stop_order`, `cancel_order`) will return rejection status
- 👍 Useful for monitoring and analysis without trading risk

### Stopping the Services

```bash
docker-compose down
```

To also remove volumes:

```bash
docker-compose down -v
```

## Development

### Building Locally

To build the Docker image locally instead of using the pre-built image:

```bash
# Build the image
docker-compose build

# Or build without cache
docker-compose build --no-cache
```

### Running Tests

The server uses standard Python testing. To run tests:

```bash
docker-compose exec mcp-server python -m pytest tests/
```

## Configuration Reference

### Complete Environment Variables Reference

See the [Configuration](#configuration) section above for detailed parameter descriptions.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `IBKR_TRADING_MODE` | string | `paper` | `paper` or `live` |
| `IBKR_USERID` | string | - | Live trading username |
| `IBKR_PASSWORD` | string | - | Live trading password |
| `IBKR_USERID_PAPER` | string | - | Paper trading username |
| `IBKR_PASSWORD_PAPER` | string | - | Paper trading password |
| `IBKR_GATEWAY_LIVE_PORT` | integer | `4003` | Live trading port |
| `IBKR_GATEWAY_PAPER_PORT` | integer | `4004` | Paper trading port |
| `SERVER_PORT` | integer | `8080` | MCP server port |
| `READONLY` | boolean | `false` | Enable read-only mode |
| `VNC_PASSWORD` | string | - | VNC password |

## Troubleshooting

### Connection Issues

If the MCP server cannot connect to the IB Gateway:

1. Check that both containers are running:
   ```bash
   docker-compose ps
   ```

2. Verify the IB Gateway is accepting connections:
   ```bash
   docker-compose logs ib-gateway
   ```

3. Ensure your IBKR credentials are correct in the `.env` file

### Authentication Issues

If you have 2FA enabled on your IBKR account:

1. The gateway will wait for 2FA completion
2. Monitor the VNC connection to complete 2FA
3. The `TWOFA_TIMEOUT_ACTION=restart` setting will restart the gateway if 2FA times out

### Paper Trading vs Live Trading

- **Paper Trading** (`IBKR_TRADING_MODE=paper`): Uses port 4004, connects to IBKR paper trading
  - ✅ **Safe for testing**
  - No real money involved
  
- **Live Trading** (`IBKR_TRADING_MODE=live`): Uses port 4003, connects to live IBKR account
  - ⚠️ **DANGER: Real money at risk!**
  - All orders affect your real account

⚠️ **Warning**: Be extremely careful when switching to live trading mode! Always test thoroughly in paper trading first.

## Market Data Subscriptions

Some APIs require market data subscriptions from Interactive Brokers:

### Required Subscriptions

- **Real-time stock quotes**: Requires subscription to the relevant exchange (NYSE, NASDAQ, etc.)
- **Options data**: Requires OPRA (Options Price Reporting Authority) subscription
- **Delayed data**: May be available for free with 15-20 minute delay depending on market

### How to Check Subscriptions

1. Log in to your IBKR account at https://www.interactivebrokers.com
2. Go to **Account Management** → **Settings** → **Market Data Subscriptions**
3. Review your active subscriptions and add any needed ones

### Without Subscriptions

Without subscriptions, the following may occur:
- `get_stock_price`: May return delayed data (15-20 min delay) or error for some markets
- `get_option_chain`: Will likely fail or return no data
- `get_historical_data`: May work for some data ranges, but real-time bars will fail

## License

MIT

## References

- [FastMCP](https://github.com/jlowin/fastmcp) - Modern Python framework for building MCP servers
- [IB Gateway Docker](https://github.com/gnzsnz/ib-gateway-docker)
- [ib_async Documentation](https://ib-api-reloaded.github.io/ib_async/readme.html)
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/index.php?f=5041)
