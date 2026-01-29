# IBKR MCP Docker

A Model Context Protocol (MCP) server that provides Interactive Brokers (IBKR) trading capabilities through Docker.

---

## ⚠️ IMPORTANT DISCLAIMER / 重要免责声明

**THIS SOFTWARE IS PROVIDED FOR INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY. BY USING THIS SOFTWARE, YOU ACKNOWLEDGE AND AGREE THAT:**

**本软件仅供信息和教育目的。使用本软件即表示您确认并同意：**

- **YOU ARE SOLELY RESPONSIBLE** for all trading decisions and operations made through this software
- **您独自承担全部责任**，包括通过本软件进行的所有交易决策和操作
- You use this software **AT YOUR OWN RISK**. The authors and contributors are not responsible for any financial losses, damages, or liabilities
- 您使用本软件需**自行承担风险**。作者和贡献者对任何财务损失、损害或责任概不负责
- This software connects to your **real financial accounts**. Improper use may result in significant financial loss
- 本软件连接您的**真实金融账户**。不当使用可能导致重大财务损失
- **ALWAYS** test with **Paper Trading** mode first before using with live accounts
- **务必**先使用**模拟交易**模式测试，然后再用于真实账户
- You should fully understand the risks of automated trading and the Interactive Brokers platform before use
- 使用前您应充分了解自动化交易的风险和盈透证券平台

**USE AT YOUR OWN RISK. NO WARRANTY OF ANY KIND.**

**风险自负，不提供任何形式的保证。**

---

## What Does This Project Do? / 项目功能

This project provides a **bridge** between the Model Context Protocol (MCP) and Interactive Brokers trading platform. It allows AI assistants and applications to:

本项目提供了**模型上下文协议 (MCP)** 和**盈透证券 (Interactive Brokers)** 交易平台之间的**桥接**。它允许 AI 助手和应用程序：

1. **Query real-time market data** - Get live stock prices, historical data, and option chains
2. **Monitor account status** - Check balances, positions, and portfolio performance
3. **Execute trades** - Place market orders, limit orders, and stop-loss orders programmatically
4. **Integrate with AI workflows** - Use natural language to interact with your brokerage account

1. **查询实时市场数据** - 获取实时股票价格、历史数据和期权链
2. **监控账户状态** - 检查余额、持仓和投资组合表现
3. **执行交易** - 以编程方式下达市场订单、限价订单和止损订单
4. **与 AI 工作流集成** - 使用自然语言与您的券商账户交互

## Features

This MCP server provides the following capabilities:

### Account Management (账户管理)
- Query account cash flow and balances
- View account summary and net liquidation value

### Position Management (持仓管理)
- Query current positions
- View unrealized and realized P&L

### Order Management (订单管理)
- Query order status (open and filled orders)
- Place limit orders
- Place market orders
- Place stop-loss orders

### Market Data (市场数据)
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

## Quick Start (Recommended: Use Pre-built Images) / 快速开始（推荐：使用预构建镜像）

**We recommend using pre-built Docker images** for easier setup and automatic updates. Pre-built images are:
- ✅ Tested and verified
- ✅ Multi-platform (amd64/arm64)
- ✅ Automatically built from releases
- ✅ No local build required

**我们推荐使用预构建的 Docker 镜像**以便于设置和自动更新。预构建镜像具有以下优点：
- ✅ 经过测试和验证
- ✅ 多平台支持 (amd64/arm64)
- ✅ 从发布版本自动构建
- ✅ 无需本地构建

### Using Pre-built Images (使用预构建镜像)

1. Create a `.env` file from the example:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your IBKR credentials (see [Configuration](#configuration) section below)

3. Update `docker-compose.yml` to use the pre-built image:
```yaml
services:
  mcp-server:
    image: ghcr.io/metaif/ibkr-mcp-docker:latest  # Use pre-built image
    # Remove the 'build: .' line
    ...
```

4. Start the services:
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

## Configuration

### Environment Variables / 环境变量

All configuration is done through the `.env` file. Here's a detailed explanation of each parameter:

所有配置通过 `.env` 文件完成。以下是每个参数的详细说明：

#### IBKR Gateway Configuration (IB 网关配置)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `IBKR_TRADING_MODE` | Trading mode: `paper` for paper trading, `live` for live trading<br/>交易模式：`paper` 为模拟交易，`live` 为实盘交易 | `paper` | Yes |
| `IBKR_USERID` | IBKR username for live trading<br/>实盘交易的 IBKR 用户名 | - | Yes (for live) |
| `IBKR_PASSWORD` | IBKR password for live trading<br/>实盘交易的 IBKR 密码 | - | Yes (for live) |
| `IBKR_USERID_PAPER` | IBKR username for paper trading<br/>模拟交易的 IBKR 用户名 | - | Yes (for paper) |
| `IBKR_PASSWORD_PAPER` | IBKR password for paper trading<br/>模拟交易的 IBKR 密码 | - | Yes (for paper) |
| `IBKR_GATEWAY_LIVE_PORT` | IB Gateway port for live trading<br/>实盘交易的 IB 网关端口 | `4003` | No |
| `IBKR_GATEWAY_PAPER_PORT` | IB Gateway port for paper trading<br/>模拟交易的 IB 网关端口 | `4004` | No |
| `VNC_PASSWORD` | VNC password for monitoring the gateway UI<br/>监控网关界面的 VNC 密码 | - | No |

#### MCP Server Configuration (MCP 服务器配置)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVER_PORT` | MCP server HTTP port. Server will be at `http://127.0.0.1:<PORT>/mcp`<br/>MCP 服务器 HTTP 端口。服务器地址为 `http://127.0.0.1:<PORT>/mcp` | `8080` | No |
| `READONLY` | Read-only mode. Set to `true`/`1`/`yes` to disable order operations<br/>只读模式。设置为 `true`/`1`/`yes` 禁用订单操作 | `false` | No |

### Configuration Example / 配置示例

Edit your `.env` file:

```bash
# For Paper Trading (模拟交易)
IBKR_TRADING_MODE=paper
IBKR_USERID_PAPER=your_paper_username
IBKR_PASSWORD_PAPER=your_paper_password
IBKR_GATEWAY_PAPER_PORT=4004

# For Live Trading (实盘交易) - BE CAREFUL!
# IBKR_TRADING_MODE=live
# IBKR_USERID=your_live_username
# IBKR_PASSWORD=your_live_password
# IBKR_GATEWAY_LIVE_PORT=4003

# MCP Server
SERVER_PORT=8080

# Safety: Enable read-only mode to prevent accidental trades
# 安全：启用只读模式以防止意外交易
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

### Available MCP API Tools / 可用的 MCP API 工具

The MCP server exposes the following tools. Each tool returns typed, validated responses using Pydantic models.

MCP 服务器提供以下工具。每个工具都使用 Pydantic 模型返回类型化、验证的响应。

#### Account & Portfolio APIs (账户和投资组合 API)

**These APIs do NOT require market data subscriptions (这些 API 不需要行情订阅):**

1. **`get_account_summary`** → `AccountSummary`
   - Get account balance and cash flow information
   - 获取账户余额和资金流信息
   - Returns: `net_liquidation`, `cash_balance`, `total_cash_value`, `buying_power`, `gross_position_value`
   - **No market data subscription required / 无需行情订阅**

2. **`get_positions`** → `List[Position]`
   - Get all current positions
   - 获取所有当前持仓
   - Each position includes: `symbol`, `quantity`, `avg_cost`, `market_price`, `unrealized_pnl`, `realized_pnl`
   - **No market data subscription required / 无需行情订阅**

3. **`get_orders`** → `List[OrderInfo]`
   - Get all orders (open and filled)
   - 获取所有订单（未完成和已完成）
   - Includes: `order_id`, `symbol`, `action`, `order_type`, `status`, `filled`, `avg_fill_price`
   - **No market data subscription required / 无需行情订阅**

#### Market Data APIs (市场数据 API)

**These APIs REQUIRE market data subscriptions (这些 API 需要行情订阅):**

4. **`get_stock_price`** → `StockPrice`
   - Get real-time stock price
   - 获取实时股票价格
   - Parameters: `symbol` (required), `exchange` (optional, default: "SMART")
   - Returns: `bid`, `ask`, `last`, `close`, `volume`, `timestamp`
   - **⚠️ REQUIRES market data subscription / 需要行情订阅**
   - **Note**: Without subscription, may return delayed data or fail for certain markets

5. **`get_historical_data`** → `List[HistoricalBar]`
   - Get historical stock data
   - 获取历史股票数据
   - Parameters: 
     - `symbol` (required)
     - `duration` (default: "1 D", e.g., "1 D", "1 W", "1 M")
     - `bar_size` (default: "1 hour", e.g., "1 min", "1 hour", "1 day")
     - `exchange` (optional)
   - Returns: OHLCV data for each bar (`date`, `open`, `high`, `low`, `close`, `volume`)
   - **May require market data subscription depending on the data requested / 根据请求的数据可能需要行情订阅**

6. **`get_option_chain`** → `List[OptionChain]`
   - Get option chain for a stock
   - 获取股票的期权链
   - Parameters: `symbol` (required), `exchange` (optional)
   - Returns: Available `strikes`, `expirations`, `multipliers`
   - **⚠️ REQUIRES market data subscription for options / 需要期权行情订阅**

#### Trading APIs (交易 API)

**These APIs do NOT require market data subscriptions but modify your account (这些 API 不需要行情订阅但会修改您的账户):**

7. **`place_limit_order`** → `OrderResult`
   - Place a limit order
   - 下达限价订单
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `limit_price`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled / 只读模式下禁用**
   - **⚠️ CAUTION: This places real orders! / 注意：这会下达真实订单！**

8. **`place_market_order`** → `OrderResult`
   - Place a market order
   - 下达市价订单
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled / 只读模式下禁用**
   - **⚠️ CAUTION: This places real orders! / 注意：这会下达真实订单！**

9. **`place_stop_order`** → `OrderResult`
   - Place a stop-loss order
   - 下达止损订单
   - Parameters: `symbol`, `action` (BUY/SELL), `quantity`, `stop_price`, `exchange` (optional)
   - **⚠️ Disabled when READONLY mode is enabled / 只读模式下禁用**
   - **⚠️ CAUTION: This places real orders! / 注意：这会下达真实订单！**

10. **`cancel_order`** → `CancelResult`
    - Cancel an existing order
    - 取消现有订单
    - Parameters: `order_id` (required)
    - **⚠️ Disabled when READONLY mode is enabled / 只读模式下禁用**

All tools use **Pydantic models** for type-safe, validated responses with clear field descriptions.

所有工具都使用 **Pydantic 模型**来提供类型安全、经过验证的响应，并具有清晰的字段描述。

### Read-Only Mode / 只读模式

Enable read-only mode to prevent order placement, modification, and cancellation:

启用只读模式以防止下单、修改订单和取消订单：

```bash
READONLY=true
```

When enabled / 启用时：
- ✅ All query operations (positions, orders, prices, etc.) work normally
- ✅ 所有查询操作（持仓、订单、价格等）正常工作
- ❌ Order placement tools (`place_limit_order`, `place_market_order`, `place_stop_order`, `cancel_order`) will return rejection status
- ❌ 订单下达工具（`place_limit_order`、`place_market_order`、`place_stop_order`、`cancel_order`）将返回拒绝状态
- 👍 Useful for monitoring and analysis without trading risk
- 👍 适用于监控和分析，无交易风险

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

### Complete Environment Variables Reference / 完整环境变量参考

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

### Paper Trading vs Live Trading / 模拟交易与实盘交易

- **Paper Trading** (`IBKR_TRADING_MODE=paper`): Uses port 4004, connects to IBKR paper trading
  - 模拟交易模式：使用端口 4004，连接到 IBKR 模拟交易
  - ✅ **Safe for testing / 安全测试**
  - No real money involved / 不涉及真实资金
  
- **Live Trading** (`IBKR_TRADING_MODE=live`): Uses port 4003, connects to live IBKR account
  - 实盘交易模式：使用端口 4003，连接到真实 IBKR 账户
  - ⚠️ **DANGER: Real money at risk! / 危险：真实资金有风险！**
  - All orders affect your real account / 所有订单都会影响您的真实账户

⚠️ **Warning / 警告**: Be extremely careful when switching to live trading mode! Always test thoroughly in paper trading first.

⚠️ **警告**：切换到实盘交易模式时务必格外小心！请务必先在模拟交易中进行彻底测试。

## Market Data Subscriptions / 行情订阅

Some APIs require market data subscriptions from Interactive Brokers:

某些 API 需要从盈透证券订阅行情数据：

### Required Subscriptions / 需要的订阅

- **Real-time stock quotes**: Requires subscription to the relevant exchange (NYSE, NASDAQ, etc.)
- **实时股票报价**：需要订阅相关交易所（NYSE、NASDAQ 等）
- **Options data**: Requires OPRA (Options Price Reporting Authority) subscription
- **期权数据**：需要订阅 OPRA（期权价格报告机构）
- **Delayed data**: May be available for free with 15-20 minute delay depending on market
- **延迟数据**：根据市场情况，可能提供 15-20 分钟延迟的免费数据

### How to Check Subscriptions / 如何查看订阅

1. Log in to your IBKR account at https://www.interactivebrokers.com
2. Go to **Account Management** → **Settings** → **Market Data Subscriptions**
3. Review your active subscriptions and add any needed ones

1. 登录您的 IBKR 账户 https://www.interactivebrokers.com
2. 转到**账户管理** → **设置** → **市场数据订阅**
3. 查看您的有效订阅并添加任何需要的订阅

### Without Subscriptions / 没有订阅时

Without subscriptions, the following may occur:
- `get_stock_price`: May return delayed data (15-20 min delay) or error for some markets
- `get_option_chain`: Will likely fail or return no data
- `get_historical_data`: May work for some data ranges, but real-time bars will fail

没有订阅时，可能会出现以下情况：
- `get_stock_price`：可能返回延迟数据（15-20 分钟延迟）或某些市场出错
- `get_option_chain`：很可能失败或不返回数据
- `get_historical_data`：某些数据范围可能有效，但实时柱状图将失败

## License

MIT

## References

- [FastMCP](https://github.com/jlowin/fastmcp) - Modern Python framework for building MCP servers
- [IB Gateway Docker](https://github.com/gnzsnz/ib-gateway-docker)
- [ib_async Documentation](https://ib-api-reloaded.github.io/ib_async/readme.html)
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/index.php?f=5041)