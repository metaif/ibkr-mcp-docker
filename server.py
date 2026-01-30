#!/usr/bin/env python3
"""
IBKR MCP Server
A Model Context Protocol server that provides IBKR trading capabilities.
"""

import os
import asyncio
import logging
import threading
from typing import List, Optional, Callable
from functools import wraps

from pydantic import BaseModel, Field
from ib_async import IB, Stock, LimitOrder, MarketOrder, StopOrder, Order, Contract
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY = "USD"
DEFAULT_EXCHANGE = "SMART"
CONNECTION_TIMEOUT = 20
MARKET_DATA_TIMEOUT = 10
ORDER_SUBMIT_DELAY = 1
AUTO_CONNECT_RETRY_INTERVAL = 5  # seconds

# IBKR connection settings from environment
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_LIVE_PORT = int(os.getenv("IBKR_GATEWAY_LIVE_PORT", "4003"))
IBKR_PAPER_PORT = int(os.getenv("IBKR_GATEWAY_PAPER_PORT", "4004"))
IBKR_TRADING_MODE = os.getenv("IBKR_TRADING_MODE", "paper").lower()
IBKR_PORT = IBKR_LIVE_PORT if IBKR_TRADING_MODE == "live" else IBKR_PAPER_PORT
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

# Read-only mode - disables order placement, modification, and cancellation
READONLY = os.getenv("READONLY", "false").lower() in ("true", "1", "yes")

# Server configuration
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Global IB connection - will be initialized on startup
ib: Optional[IB] = None
_connection_lock = asyncio.Lock()

# Create FastMCP server
mcp = FastMCP("IBKR Trading Server")


# Pydantic Models for structured returns
class AccountValue(BaseModel):
    """Account value information"""
    tag: str
    value: str
    currency: str
    account: str


class AccountSummary(BaseModel):
    """Account summary with key financial metrics"""
    net_liquidation: Optional[AccountValue] = None
    cash_balance: Optional[AccountValue] = None
    total_cash_value: Optional[AccountValue] = None
    buying_power: Optional[AccountValue] = None
    gross_position_value: Optional[AccountValue] = None


class Position(BaseModel):
    """Position information"""
    account: str
    symbol: str
    sec_type: str = Field(description="Security type (STK, OPT, FUT, etc.)")
    exchange: str
    position: float = Field(description="Number of shares/contracts")
    avg_cost: float = Field(description="Average cost per share")
    market_price: float = Field(description="Current market price")
    market_value: float = Field(description="Total market value")
    unrealized_pnl: float = Field(description="Unrealized profit/loss")
    realized_pnl: float = Field(description="Realized profit/loss")


class OrderInfo(BaseModel):
    """Order information"""
    order_id: int
    symbol: str
    action: str = Field(description="BUY or SELL")
    order_type: str = Field(description="Order type (LMT, MKT, STP, etc.)")
    total_quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = Field(description="Order status")
    filled: float = Field(description="Filled quantity")
    remaining: float = Field(description="Remaining quantity")
    avg_fill_price: float = Field(description="Average fill price")


class StockPrice(BaseModel):
    """Real-time stock price information"""
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    timestamp: Optional[str] = None


class HistoricalBar(BaseModel):
    """Historical price bar"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class OptionChain(BaseModel):
    """Option chain information"""
    exchange: str
    strikes: List[float]
    expirations: List[str]
    multiplier: str


class OrderResult(BaseModel):
    """Result of order placement"""
    order_id: int
    status: str
    symbol: str
    action: str
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None


class CancelResult(BaseModel):
    """Result of order cancellation"""
    order_id: int
    status: str
    message: str


# Helper functions
async def ensure_connected() -> IB:
    """Ensure IB connection is active."""
    global ib
    
    async with _connection_lock:
        if ib is None:
            ib = IB()
        
        if not ib.isConnected():
            try:
                logger.info(f"Connecting to IB Gateway at {IBKR_HOST}:{IBKR_PORT}")
                await ib.connectAsync(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=CONNECTION_TIMEOUT)
                logger.info(f"Connected to IB Gateway at {IBKR_HOST}:{IBKR_PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to IB Gateway: {e}")
                raise
    
    return ib


async def create_and_qualify_contract(symbol: str, exchange: str = DEFAULT_EXCHANGE) -> Contract:
    """Create and qualify a stock contract."""
    ib_conn = await ensure_connected()
    contract = Stock(symbol, exchange, DEFAULT_CURRENCY)
    await ib_conn.qualifyContractsAsync(contract)
    return contract


async def place_order_internal(
    symbol: str, 
    action: str, 
    quantity: float,
    order: Order, 
    exchange: str = DEFAULT_EXCHANGE,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None
) -> OrderResult:
    """Internal function to place an order."""
    ib_conn = await ensure_connected()
    contract = await create_and_qualify_contract(symbol, exchange)
    
    trade = ib_conn.placeOrder(contract, order)
    await asyncio.sleep(ORDER_SUBMIT_DELAY)
    
    return OrderResult(
        order_id=trade.order.orderId,
        status=trade.orderStatus.status,
        symbol=symbol,
        action=action,
        quantity=quantity,
        limit_price=limit_price,
        stop_price=stop_price
    )


def safe_float(value, default: Optional[float] = None) -> Optional[float]:
    """Safely convert value to float, handling None and zero/negative values."""
    if value is None:
        return default
    if isinstance(value, (int, float)) and value <= 0:
        return default
    return float(value)


def readonly_protected(func: Callable) -> Callable:
    """Decorator to protect write operations in readonly mode."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if READONLY:
            # Extract order parameters from args/kwargs
            symbol = kwargs.get('symbol', args[0] if args else 'unknown')
            action = kwargs.get('action', args[1] if len(args) > 1 else 'unknown')
            quantity = kwargs.get('quantity', args[2] if len(args) > 2 else 0)
            limit_price = kwargs.get('limit_price')
            stop_price = kwargs.get('stop_price')
            
            return OrderResult(
                order_id=0,
                status="REJECTED",
                symbol=symbol,
                action=action,
                quantity=quantity,
                limit_price=limit_price,
                stop_price=stop_price
            )
        return await func(*args, **kwargs)
    return wrapper


async def auto_connect_ibkr():
    """Automatically connect to IBKR Gateway with retry logic."""
    while True:
        try:
            logger.info("Attempting to connect to IBKR Gateway...")
            await ensure_connected()
            logger.info("Successfully connected to IBKR Gateway")
            break
        except Exception as e:
            logger.warning(
                f"Failed to connect to IBKR Gateway: {e}. "
                f"Retrying in {AUTO_CONNECT_RETRY_INTERVAL} seconds..."
            )
            await asyncio.sleep(AUTO_CONNECT_RETRY_INTERVAL)


def extract_position_data(pos, pnl):
    """Extract position data from position and PnL objects."""
    market_value = getattr(pnl, 'value', 0.0) if pnl else 0.0
    unrealized_pnl = getattr(pnl, 'unrealizedPnL', 0.0) if pnl else 0.0
    realized_pnl = getattr(pnl, 'realizedPnL', 0.0) if pnl else 0.0
    market_price = market_value / pos.position if pnl and pos.position != 0 else 0.0
    
    return Position(
        account=pos.account,
        symbol=pos.contract.symbol,
        sec_type=pos.contract.secType,
        exchange=pos.contract.primaryExchange or pos.contract.exchange,
        position=pos.position,
        avg_cost=pos.avgCost,
        market_price=market_price,
        market_value=market_value,
        unrealized_pnl=unrealized_pnl,
        realized_pnl=realized_pnl
    )


# MCP Tools

@mcp.tool()
async def get_account_summary() -> AccountSummary:
    """Get account summary including cash balance and net liquidation value"""
    ib_conn = await ensure_connected()
    
    # Use async method to get account summary
    account_values = await ib_conn.accountSummaryAsync()
    
    required_tags = {'NetLiquidation', 'CashBalance', 'TotalCashValue', 'BuyingPower', 'GrossPositionValue'}
    summary_dict = {}
    
    for av in account_values:
        if av.tag in required_tags:
            summary_dict[av.tag] = AccountValue(
                tag=av.tag,
                value=av.value,
                currency=av.currency,
                account=av.account
            )
    
    return AccountSummary(
        net_liquidation=summary_dict.get('NetLiquidation'),
        cash_balance=summary_dict.get('CashBalance'),
        total_cash_value=summary_dict.get('TotalCashValue'),
        buying_power=summary_dict.get('BuyingPower'),
        gross_position_value=summary_dict.get('GrossPositionValue')
    )


@mcp.tool()
async def get_positions() -> List[Position]:
    """Get all current positions in the account"""
    ib_conn = await ensure_connected()
    
    # Get positions and PnL data
    positions = ib_conn.positions()
    pnl_singles = ib_conn.pnlSingle()
    
    # Create a map of (account, conId) -> pnlSingle for easy lookup
    pnl_map = {(p.account, p.conId): p for p in pnl_singles}
    
    result = []
    for pos in positions:
        # Get matching pnl data
        pnl = pnl_map.get((pos.account, pos.contract.conId))
        
        # Calculate values
        market_price = 0.0
        market_value = 0.0
        unrealized_pnl = 0.0
        realized_pnl = 0.0
        
        if pnl:
            market_value = pnl.value if hasattr(pnl, 'value') else 0.0
            unrealized_pnl = pnl.unrealizedPnL if hasattr(pnl, 'unrealizedPnL') else 0.0
            realized_pnl = pnl.realizedPnL if hasattr(pnl, 'realizedPnL') else 0.0
            # Calculate market price from value and position
            if pos.position != 0:
                market_price = market_value / pos.position
        
        result.append(Position(
            account=pos.account,
            symbol=pos.contract.symbol,
            sec_type=pos.contract.secType,
            exchange=pos.contract.primaryExchange or pos.contract.exchange,
            position=pos.position,
            avg_cost=pos.avgCost,
            market_price=market_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl
        ))
    
    return result


@mcp.tool()
async def get_orders() -> List[OrderInfo]:
    """Get all orders (open and filled)"""
    ib_conn = await ensure_connected()
    
    # Get all trades (includes open and recently filled)
    all_trades = ib_conn.trades()
    
    result = []
    for trade in all_trades:
        result.append(OrderInfo(
            order_id=trade.order.orderId,
            symbol=trade.contract.symbol,
            action=trade.order.action,
            order_type=trade.order.orderType,
            total_quantity=trade.order.totalQuantity,
            limit_price=trade.order.lmtPrice or None,
            stop_price=trade.order.auxPrice or None,
            status=trade.orderStatus.status,
            filled=trade.orderStatus.filled,
            remaining=trade.orderStatus.remaining,
            avg_fill_price=trade.orderStatus.avgFillPrice
        ))
    
    return result


@mcp.tool()
async def get_stock_price(symbol: str, exchange: str = DEFAULT_EXCHANGE) -> StockPrice:
    """
    Get real-time stock price
    
    Args:
        symbol: Stock symbol (e.g., AAPL, TSLA)
        exchange: Exchange (default: SMART)
    """
    ib_conn = await ensure_connected()
    contract = await create_and_qualify_contract(symbol, exchange)

    # 1 = Live, 2 = Frozen, 3 = Delayed, 4 = Delayed Frozen
    ib_conn.reqMarketDataType(2)

    ticker = ib_conn.reqMktData(contract, '', snapshot=True, regulatorySnapshot=False)
    
    # Wait for ticker update
    update_event = asyncio.Event()
    
    def on_ticker_update(ticker):
        if ticker.last or ticker.close or ticker.bid or ticker.ask:
            update_event.set()
    
    ticker.updateEvent += on_ticker_update
    
    try:
        await asyncio.wait_for(update_event.wait(), timeout=MARKET_DATA_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout waiting for market data for {symbol}")
    finally:
        ticker.updateEvent -= on_ticker_update
        ib_conn.cancelMktData(contract)
    
    return StockPrice(
        symbol=symbol,
        bid=safe_float(ticker.bid),
        ask=safe_float(ticker.ask),
        last=safe_float(ticker.last),
        close=safe_float(ticker.close),
        volume=safe_float(ticker.volume),
        timestamp=str(ticker.time) if ticker.time else None
    )


@mcp.tool()
async def get_historical_data(
    symbol: str, 
    duration: str = "1 D",
    bar_size: str = "1 hour",
    exchange: str = DEFAULT_EXCHANGE
) -> List[HistoricalBar]:
    """
    Get historical stock data
    
    Args:
        symbol: Stock symbol
        duration: Duration (e.g., '1 D', '1 W', '1 M')
        bar_size: Bar size (e.g., '1 min', '1 hour', '1 day')
        exchange: Exchange (default: SMART)
    """
    ib_conn = await ensure_connected()
    contract = await create_and_qualify_contract(symbol, exchange)
    
    try:
        bars = await ib_conn.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True
        )
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        raise ValueError(f"Failed to fetch historical data for {symbol}: {str(e)}")
    
    return [
        HistoricalBar(
            date=str(bar.date),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume
        )
        for bar in bars
    ]


@mcp.tool()
async def get_option_chain(symbol: str, exchange: str = DEFAULT_EXCHANGE) -> List[OptionChain]:
    """
    Get option chain for a stock
    
    Args:
        symbol: Stock symbol
        exchange: Exchange (default: SMART)
    """
    ib_conn = await ensure_connected()
    contract = await create_and_qualify_contract(symbol, exchange)
    
    chains = await ib_conn.reqSecDefOptParamsAsync(
        contract.symbol, '', contract.secType, contract.conId
    )
    
    return [
        OptionChain(
            exchange=chain.exchange,
            strikes=sorted(list(chain.strikes)),
            expirations=sorted([str(exp) for exp in chain.expirations]),
            multiplier=str(chain.multiplier)
        )
        for chain in (chains or [])
    ]


@mcp.tool()
@readonly_protected
async def place_limit_order(
    symbol: str,
    action: str,
    quantity: float,
    limit_price: float,
    exchange: str = DEFAULT_EXCHANGE
) -> OrderResult:
    """
    Place a limit order
    
    Args:
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares
        limit_price: Limit price
        exchange: Exchange (default: SMART)
    
    Note: This tool is disabled when READONLY mode is enabled
    """
    order = LimitOrder(action, quantity, limit_price)
    return await place_order_internal(symbol, action, quantity, order, exchange, limit_price=limit_price)


@mcp.tool()
@readonly_protected
async def place_market_order(
    symbol: str,
    action: str,
    quantity: float,
    exchange: str = DEFAULT_EXCHANGE
) -> OrderResult:
    """
    Place a market order
    
    Args:
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares
        exchange: Exchange (default: SMART)
    
    Note: This tool is disabled when READONLY mode is enabled
    """
    order = MarketOrder(action, quantity)
    return await place_order_internal(symbol, action, quantity, order, exchange)


@mcp.tool()
@readonly_protected
async def place_stop_order(
    symbol: str,
    action: str,
    quantity: float,
    stop_price: float,
    exchange: str = DEFAULT_EXCHANGE
) -> OrderResult:
    """
    Place a stop (stop-loss) order
    
    Args:
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares
        stop_price: Stop price
        exchange: Exchange (default: SMART)
    
    Note: This tool is disabled when READONLY mode is enabled
    """
    order = StopOrder(action, quantity, stop_price)
    return await place_order_internal(symbol, action, quantity, order, exchange, stop_price=stop_price)


@mcp.tool()
async def cancel_order(order_id: int) -> CancelResult:
    """
    Cancel an existing order
    
    Args:
        order_id: Order ID to cancel
    
    Note: This tool is disabled when READONLY mode is enabled
    """
    if READONLY:
        return CancelResult(
            order_id=order_id,
            status="REJECTED",
            message="Order cancellation is disabled in READONLY mode"
        )
    
    ib_conn = await ensure_connected()
    
    # Find the trade with this order_id
    target_trade = next(
        (t for t in ib_conn.trades() if t.order.orderId == order_id), 
        None
    )
    
    if target_trade is None:
        return CancelResult(
            order_id=order_id,
            status="NOT_FOUND",
            message=f"Order {order_id} not found"
        )
    
    # Cancel the order
    ib_conn.cancelOrder(target_trade.order)
    await asyncio.sleep(ORDER_SUBMIT_DELAY)
    
    # Check the updated status
    updated_status = target_trade.orderStatus.status
    
    return CancelResult(
        order_id=order_id,
        status=updated_status,
        message=f"Order {order_id} cancellation requested. Status: {updated_status}"
    )


if __name__ == "__main__":
    logger.info(
        f"Starting IBKR MCP Server in {'READONLY' if READONLY else 'READ/WRITE'} mode"
    )
    
    def start_auto_connect():
        """Start auto-connect in a new event loop in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(auto_connect_ibkr())
        loop.close()
    
    # Start auto-connect in background thread
    connect_thread = threading.Thread(target=start_auto_connect, daemon=True)
    connect_thread.start()
    
    # Run the MCP server (this will block)
    mcp.run(transport="http", host="0.0.0.0", port=SERVER_PORT)
