# IBKR MCP Docker

中文 | [English](README.md)

一个通过 Docker 提供盈透证券 (IBKR) 交易功能的模型上下文协议 (MCP) 服务器。

---

## ⚠️ 重要免责声明

**本软件仅供信息和教育目的。使用本软件即表示您确认并同意：**

- **您独自承担全部责任**，包括通过本软件进行的所有交易决策和操作
- 您使用本软件需**自行承担风险**。作者和贡献者对任何财务损失、损害或责任概不负责
- 本软件连接您的**真实金融账户**。不当使用可能导致重大财务损失
- **务必**先使用**模拟交易**模式测试，然后再用于真实账户
- 使用前您应充分了解自动化交易的风险和盈透证券平台

**风险自负，不提供任何形式的保证。**

---

## 项目功能

本项目提供了**模型上下文协议 (MCP)** 和**盈透证券 (Interactive Brokers)** 交易平台之间的**桥接**。它允许 AI 助手和应用程序：

1. **查询实时市场数据** - 获取实时股票价格、历史数据和期权链
2. **监控账户状态** - 检查余额、持仓和投资组合表现
3. **执行交易** - 以编程方式下达市场订单、限价订单和止损订单
4. **与 AI 工作流集成** - 使用自然语言与您的券商账户交互

## 功能特性

本 MCP 服务器提供以下功能：

### 账户管理
- 查询账户资金流和余额
- 查看账户摘要和净清算价值

### 持仓管理
- 查询当前持仓
- 查看未实现和已实现盈亏

### 订单管理
- 查询订单状态（未完成和已完成订单）
- 下达限价订单
- 下达市价订单
- 下达止损订单

### 市场数据
- 获取实时股票价格 *（需要行情订阅）*
- 查询历史股票数据
- 访问期权链 *（需要行情订阅）*

## 架构

本项目集成了两个服务：

1. **IB Gateway** - 使用 [ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker) 提供盈透证券网关
2. **MCP 服务器** - 基于 [FastMCP](https://github.com/jlowin/fastmcp) 和 [ib_async](https://ib-api-reloaded.github.io/ib_async/readme.html) 构建的 Python MCP 服务器

**主要特性：**
- **FastMCP 集成**：使用基于装饰器的工具注册，代码简洁优雅
- **Pydantic 模型**：所有响应使用 Pydantic 模型进行类型化，提供结构化、验证的数据
- **类型安全**：完整的类型提示和从函数签名自动生成的模式
- **HTTP/SSE 传输**：通过 HTTP 在 `http://127.0.0.1:8080/mcp` 暴露 MCP 服务器
- **只读模式**：可选的只读模式，禁用订单下达、修改和取消

两个服务都通过单个 `.env` 文件配置，简单易用。

## 前置要求

- Docker 和 Docker Compose
- 盈透证券账户（模拟交易或实盘）
- IBKR 账户凭证
- **行情订阅**（实时价格数据和期权数据所需）

> **注意**：某些功能需要有效的 IBKR 行情订阅。没有订阅时，您可能收到延迟数据或某些市场无数据。

## 快速开始（推荐：使用预构建镜像）

**我们推荐使用预构建的 Docker 镜像**以便于设置和自动更新。预构建镜像具有以下优点：
- ✅ 经过测试和验证
- ✅ 多平台支持 (amd64/arm64)
- ✅ 从发布版本自动构建
- ✅ 无需本地构建

### 使用预构建镜像

1. 从示例创建 `.env` 文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的 IBKR 凭证（参见下面的[配置](#配置)部分）

3. 启动服务：
```bash
docker-compose up -d
```

### 备选方案：从源码构建

如果您更喜欢从源码构建：

1. 克隆此仓库：
```bash
git clone https://github.com/metaif/ibkr-mcp-docker.git
cd ibkr-mcp-docker
```

2. 从示例创建 `.env` 文件：
```bash
cp .env.example .env
```

3. 编辑 `.env` 文件，填入您的 IBKR 凭证：
```bash
# IBKR 网关配置
IBKR_USERID=your_username
IBKR_PASSWORD=your_password
IBKR_TRADING_MODE=paper  # 或 'live' 表示实盘交易
IBKR_GATEWAY_PORT=4002

# MCP 服务器配置
SERVER_PORT=8080  # MCP 服务器将在 http://127.0.0.1:8080/mcp 可用

# 只读模式（可选）
READONLY=false  # 设置为 'true' 禁用订单操作

# 可选：用于监控网关的 VNC 密码
VNC_PASSWORD=your_vnc_password
```

4. 更新 `docker-compose.yml` 从源码构建：

   将镜像行替换为构建配置：

```yaml
services:
  mcp-server:
    build: .
    # 删除或注释掉：image: ghcr.io/metaif/ibkr-mcp-docker:latest
```

5. 构建并启动服务：
```bash
docker-compose up -d --build
```

## 配置

### 环境变量

所有配置通过 `.env` 文件完成。以下是每个参数的详细说明：

#### IB 网关配置

| 变量 | 说明 | 默认值 | 是否必需 |
|------|------|--------|----------|
| `IBKR_TRADING_MODE` | 交易模式：`paper` 为模拟交易，`live` 为实盘交易 | `paper` | 是 |
| `IBKR_USERID` | 实盘交易的 IBKR 用户名 | - | 是（实盘） |
| `IBKR_PASSWORD` | 实盘交易的 IBKR 密码 | - | 是（实盘） |
| `IBKR_USERID_PAPER` | 模拟交易的 IBKR 用户名 | - | 是（模拟） |
| `IBKR_PASSWORD_PAPER` | 模拟交易的 IBKR 密码 | - | 是（模拟） |
| `IBKR_GATEWAY_LIVE_PORT` | 实盘交易的 IB 网关端口 | `4003` | 否 |
| `IBKR_GATEWAY_PAPER_PORT` | 模拟交易的 IB 网关端口 | `4004` | 否 |
| `VNC_PASSWORD` | 监控网关界面的 VNC 密码 | - | 否 |

#### MCP 服务器配置

| 变量 | 说明 | 默认值 | 是否必需 |
|------|------|--------|----------|
| `SERVER_PORT` | MCP 服务器 HTTP 端口。服务器地址为 `http://127.0.0.1:<PORT>/mcp` | `8080` | 否 |
| `READONLY` | 只读模式。设置为 `true`/`1`/`yes` 禁用订单操作 | `false` | 否 |

### 配置示例

编辑您的 `.env` 文件：

```bash
# 模拟交易
IBKR_TRADING_MODE=paper
IBKR_USERID_PAPER=your_paper_username
IBKR_PASSWORD_PAPER=your_paper_password
IBKR_GATEWAY_PAPER_PORT=4004

# 实盘交易 - 小心！
# IBKR_TRADING_MODE=live
# IBKR_USERID=your_live_username
# IBKR_PASSWORD=your_live_password
# IBKR_GATEWAY_LIVE_PORT=4003

# MCP 服务器
SERVER_PORT=8080

# 安全：启用只读模式以防止意外交易
READONLY=true

# 可选：VNC 监控
VNC_PASSWORD=12345678
```

## 使用

### 启动服务

启动 IB Gateway 和 MCP 服务器：

```bash
docker-compose up -d
```

这将：
- 启动 IB Gateway 容器并连接到 IBKR
- 启动 MCP 服务器容器
- 在 `http://127.0.0.1:8080/mcp` 暴露 MCP 服务器

### 使用 MCP 服务器

MCP 服务器可通过 HTTP/SSE 访问：

```bash
# 访问 MCP 端点
curl http://localhost:8080/mcp
```

该端点与基于 HTTP 的 MCP 客户端兼容，可以集成到您的应用程序中。

### 监控

您可以使用 VNC 在端口 5900 监控 IB Gateway：

```bash
# 使用 VNC 客户端连接到：
localhost:5900
```

查看日志：

```bash
# 所有服务
docker-compose logs -f

# 仅 MCP 服务器
docker-compose logs -f mcp-server

# 仅 IB Gateway
docker-compose logs -f ib-gateway
```

### 可用的 MCP API 工具

MCP 服务器提供以下工具。每个工具都使用 Pydantic 模型返回类型化、验证的响应。

#### 账户和投资组合 API

**这些 API 不需要行情订阅：**

1. **`get_account_summary`** → `AccountSummary`
   - 获取账户余额和资金流信息
   - 返回：`net_liquidation`、`cash_balance`、`total_cash_value`、`buying_power`、`gross_position_value`
   - **无需行情订阅**

2. **`get_positions`** → `List[Position]`
   - 获取所有当前持仓
   - 每个持仓包括：`symbol`、`quantity`、`avg_cost`、`market_price`、`unrealized_pnl`、`realized_pnl`
   - **无需行情订阅**

3. **`get_orders`** → `List[OrderInfo]`
   - 获取所有订单（未完成和已完成）
   - 包括：`order_id`、`symbol`、`action`、`order_type`、`status`、`filled`、`avg_fill_price`
   - **无需行情订阅**

#### 市场数据 API

**这些 API 需要行情订阅：**

4. **`get_stock_price`** → `StockPrice`
   - 获取实时股票价格
   - 参数：`symbol`（必需）、`exchange`（可选，默认："SMART"）
   - 返回：`bid`、`ask`、`last`、`close`、`volume`、`timestamp`
   - **⚠️ 需要行情订阅**
   - **注意**：没有订阅时，可能返回延迟数据或某些市场失败

5. **`get_historical_data`** → `List[HistoricalBar]`
   - 获取历史股票数据
   - 参数：`symbol`（必需）、`duration`（默认："1 D"）、`bar_size`（默认："1 hour"）、`exchange`（可选）
   - 返回：每个柱状图的 OHLCV 数据（`date`、`open`、`high`、`low`、`close`、`volume`）
   - **根据请求的数据可能需要行情订阅**

6. **`get_option_chain`** → `List[OptionChain]`
   - 获取股票的期权链
   - 参数：`symbol`（必需）、`exchange`（可选）
   - 返回：可用的 `strikes`、`expirations`、`multipliers`
   - **⚠️ 需要期权行情订阅**

#### 交易 API

**这些 API 不需要行情订阅但会修改您的账户：**

7. **`place_limit_order`** → `OrderResult`
   - 下达限价订单
   - 参数：`symbol`、`action`（BUY/SELL）、`quantity`、`limit_price`、`exchange`（可选）
   - **⚠️ 只读模式下禁用**
   - **⚠️ 注意：这会下达真实订单！**

8. **`place_market_order`** → `OrderResult`
   - 下达市价订单
   - 参数：`symbol`、`action`（BUY/SELL）、`quantity`、`exchange`（可选）
   - **⚠️ 只读模式下禁用**
   - **⚠️ 注意：这会下达真实订单！**

9. **`place_stop_order`** → `OrderResult`
   - 下达止损订单
   - 参数：`symbol`、`action`（BUY/SELL）、`quantity`、`stop_price`、`exchange`（可选）
   - **⚠️ 只读模式下禁用**
   - **⚠️ 注意：这会下达真实订单！**

10. **`cancel_order`** → `CancelResult`
    - 取消现有订单
    - 参数：`order_id`（必需）
    - **⚠️ 只读模式下禁用**

所有工具都使用 **Pydantic 模型**来提供类型安全、经过验证的响应，并具有清晰的字段描述。

### 只读模式

启用只读模式以防止下单、修改订单和取消订单：

```bash
READONLY=true
```

启用时：
- ✅ 所有查询操作（持仓、订单、价格等）正常工作
- ❌ 订单下达工具（`place_limit_order`、`place_market_order`、`place_stop_order`、`cancel_order`）将返回拒绝状态
- 👍 适用于监控和分析，无交易风险

### 停止服务

```bash
docker-compose down
```

同时删除卷：

```bash
docker-compose down -v
```

## 配置参考

### 完整环境变量参考

详细参数描述请参见上面的[配置](#配置)部分。

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `IBKR_TRADING_MODE` | string | `paper` | `paper` 或 `live` |
| `IBKR_USERID` | string | - | 实盘交易用户名 |
| `IBKR_PASSWORD` | string | - | 实盘交易密码 |
| `IBKR_USERID_PAPER` | string | - | 模拟交易用户名 |
| `IBKR_PASSWORD_PAPER` | string | - | 模拟交易密码 |
| `IBKR_GATEWAY_LIVE_PORT` | integer | `4003` | 实盘交易端口 |
| `IBKR_GATEWAY_PAPER_PORT` | integer | `4004` | 模拟交易端口 |
| `SERVER_PORT` | integer | `8080` | MCP 服务器端口 |
| `READONLY` | boolean | `false` | 启用只读模式 |
| `VNC_PASSWORD` | string | - | VNC 密码 |

## 故障排除

### 连接问题

如果 MCP 服务器无法连接到 IB Gateway：

1. 检查两个容器是否都在运行：
   ```bash
   docker-compose ps
   ```

2. 验证 IB Gateway 是否接受连接：
   ```bash
   docker-compose logs ib-gateway
   ```

3. 确保 `.env` 文件中的 IBKR 凭证正确

### 认证问题

如果您的 IBKR 账户启用了双因素认证：

1. 网关将等待双因素认证完成
2. 通过 VNC 连接监控以完成双因素认证
3. `TWOFA_TIMEOUT_ACTION=restart` 设置将在双因素认证超时时重启网关

### 模拟交易与实盘交易

- **模拟交易**（`IBKR_TRADING_MODE=paper`）：使用端口 4004，连接到 IBKR 模拟交易
  - ✅ **安全测试**
  - 不涉及真实资金
  
- **实盘交易**（`IBKR_TRADING_MODE=live`）：使用端口 4003，连接到真实 IBKR 账户
  - ⚠️ **危险：真实资金有风险！**
  - 所有订单都会影响您的真实账户

⚠️ **警告**：切换到实盘交易模式时务必格外小心！请务必先在模拟交易中进行彻底测试。

## 行情订阅

某些 API 需要从盈透证券订阅行情数据：

### 需要的订阅

- **实时股票报价**：需要订阅相关交易所（NYSE、NASDAQ 等）
- **期权数据**：需要订阅 OPRA（期权价格报告机构）
- **延迟数据**：根据市场情况，可能提供 15-20 分钟延迟的免费数据

### 如何查看订阅

1. 登录您的 IBKR 账户 https://www.interactivebrokers.com
2. 转到**账户管理** → **设置** → **市场数据订阅**
3. 查看您的有效订阅并添加任何需要的订阅

### 没有订阅时

没有订阅时，可能会出现以下情况：
- `get_stock_price`：可能返回延迟数据（15-20 分钟延迟）或某些市场出错
- `get_option_chain`：很可能失败或不返回数据
- `get_historical_data`：某些数据范围可能有效，但实时柱状图将失败

## 许可证

MIT

## 参考

- [FastMCP](https://github.com/jlowin/fastmcp) - 用于构建 MCP 服务器的现代 Python 框架
- [IB Gateway Docker](https://github.com/gnzsnz/ib-gateway-docker)
- [ib_async 文档](https://ib-api-reloaded.github.io/ib_async/readme.html)
- [Pydantic](https://docs.pydantic.dev/) - 使用 Python 类型提示进行数据验证
- [模型上下文协议](https://modelcontextprotocol.io/)
- [盈透证券 API](https://www.interactivebrokers.com/en/index.php?f=5041)
