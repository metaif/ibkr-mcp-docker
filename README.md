# IBKR MCP Docker

A Model Context Protocol (MCP) server that provides Interactive Brokers (IBKR) trading capabilities through Docker.

## Features

This MCP server provides the following capabilities:

- **Account Management**
  - Query account cash flow and balances
  - View account summary and net liquidation value

- **Position Management**
  - Query current positions
  - View unrealized and realized P&L

- **Order Management**
  - Query order status (open and filled orders)
  - Place limit orders
  - Place market orders
  - Place stop-loss orders

- **Market Data**
  - Get real-time stock prices
  - Query historical stock data
  - Access option chains

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

## Setup

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

## Configuration

### MCP Server Endpoint

The MCP server is exposed via HTTP/SSE at:
```
http://127.0.0.1:8080/mcp
```

You can change the port by setting `SERVER_PORT` in your `.env` file.

### Read-Only Mode

Enable read-only mode to prevent order placement, modification, and cancellation:

```bash
READONLY=true
```

When enabled:
- All query operations (positions, orders, prices, etc.) work normally
- Order placement tools (`place_limit_order`, `place_market_order`, `place_stop_order`) will raise an error
- Useful for monitoring and analysis without trading risk

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

### Available Tools

The MCP server provides the following tools with structured Pydantic model responses:

1. **get_account_summary** → `AccountSummary`
   - Get account balance and cash flow information
   - Returns structured data with net_liquidation, cash_balance, total_cash_value, buying_power, gross_position_value

2. **get_positions** → `List[Position]`
   - Get all current positions
   - Each position includes symbol, quantity, avg_cost, market_price, unrealized_pnl, realized_pnl

3. **get_orders** → `List[OrderInfo]`
   - Get all orders (open and filled)
   - Includes order_id, symbol, action, order_type, status, filled quantity, avg_fill_price

4. **get_stock_price** → `StockPrice`
   - Get real-time stock price
   - Parameters: `symbol`, `exchange` (optional, default: "SMART")
   - Returns bid, ask, last, close, volume, timestamp

5. **get_historical_data** → `List[HistoricalBar]`
   - Get historical stock data
   - Parameters: `symbol`, `duration` (default: "1 D"), `bar_size` (default: "1 hour"), `exchange` (optional)
   - Returns OHLCV data for each bar

6. **get_option_chain** → `List[OptionChain]`
   - Get option chain for a stock
   - Parameters: `symbol`, `exchange` (optional)
   - Returns available strikes, expirations, and multipliers

7. **place_limit_order** → `OrderResult`
   - Place a limit order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `limit_price`, `exchange` (optional)
   - **Note**: Disabled when READONLY mode is enabled

8. **place_market_order** → `OrderResult`
   - Place a market order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `exchange` (optional)
   - **Note**: Disabled when READONLY mode is enabled

9. **place_stop_order** → `OrderResult`
   - Place a stop-loss order
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `stop_price`, `exchange` (optional)
   - **Note**: Disabled when READONLY mode is enabled

All tools use **Pydantic models** for type-safe, validated responses with clear field descriptions.

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

```bash
docker-compose build
```

### Running Tests

The server uses standard Python testing. To run tests:

```bash
docker-compose exec mcp-server python -m pytest tests/
```

## Configuration Reference

### Environment Variables

All configuration is done through the `.env` file:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `IBKR_USERID` | IBKR username | - | Yes |
| `IBKR_PASSWORD` | IBKR password | - | Yes |
| `IBKR_TRADING_MODE` | Trading mode: `paper` or `live` | `paper` | No |
| `IBKR_GATEWAY_PORT` | IB Gateway port | `4002` | No |
| `VNC_PASSWORD` | VNC password for monitoring | - | No |

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

- **Paper Trading** (`IBKR_TRADING_MODE=paper`): Uses port 4002, connects to IBKR paper trading
- **Live Trading** (`IBKR_TRADING_MODE=live`): Uses port 4001, connects to live IBKR account

⚠️ **Warning**: Be careful when switching to live trading mode!

## License

MIT

## References

- [FastMCP](https://github.com/jlowin/fastmcp) - Modern Python framework for building MCP servers
- [IB Gateway Docker](https://github.com/gnzsnz/ib-gateway-docker)
- [ib_async Documentation](https://ib-api-reloaded.github.io/ib_async/readme.html)
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/index.php?f=5041)