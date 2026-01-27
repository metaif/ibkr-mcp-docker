#!/usr/bin/env python3
"""
IBKR MCP Server
A Model Context Protocol server that provides IBKR trading capabilities.
"""

import os
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field
from ib_async import IB, Stock, LimitOrder, MarketOrder, StopOrder
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IBKR connection settings from environment
IBKR_HOST = os.getenv("IBKR_HOST", "ib-gateway")
IBKR_PORT = int(os.getenv("IBKR_GATEWAY_PORT", "4002"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

# Read-only mode - disables order placement, modification, and cancellation
READONLY = os.getenv("READONLY", "false").lower() in ("true", "1", "yes")

# Server configuration
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Global IB connection
ib = IB()

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


async def ensure_connected():
    """Ensure IB connection is active."""
    if not ib.isConnected():
        try:
            await ib.connectAsync(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
            logger.info(f"Connected to IB Gateway at {IBKR_HOST}:{IBKR_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to IB Gateway: {e}")
            raise


@mcp.tool()
async def get_account_summary() -> AccountSummary:
    """Get account summary including cash balance and net liquidation value"""
    await ensure_connected()
    
    account_values = ib.accountValues()
    summary_dict = {}
    
    for av in account_values:
        if av.tag in ['NetLiquidation', 'CashBalance', 'TotalCashValue', 
                      'BuyingPower', 'GrossPositionValue']:
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
    await ensure_connected()
    
    positions = ib.positions()
    result = []
    
    for pos in positions:
        result.append(Position(
            account=pos.account,
            symbol=pos.contract.symbol,
            sec_type=pos.contract.secType,
            exchange=pos.contract.exchange,
            position=pos.position,
            avg_cost=pos.avgCost,
            market_price=pos.marketPrice,
            market_value=pos.marketValue,
            unrealized_pnl=pos.unrealizedPNL,
            realized_pnl=pos.realizedPNL
        ))
    
    return result


@mcp.tool()
async def get_orders() -> List[OrderInfo]:
    """Get all orders (open and filled)"""
    await ensure_connected()
    
    trades = ib.trades()
    result = []
    
    for trade in trades:
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
async def get_stock_price(symbol: str, exchange: str = "SMART") -> StockPrice:
    """
    Get real-time stock price
    
    Args:
        symbol: Stock symbol (e.g., AAPL, TSLA)
        exchange: Exchange (default: SMART)
    """
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    ticker = ib.reqMktData(contract)
    await asyncio.sleep(2)  # Wait for data
    ib.cancelMktData(contract)
    
    return StockPrice(
        symbol=symbol,
        bid=ticker.bid or None,
        ask=ticker.ask or None,
        last=ticker.last or None,
        close=ticker.close or None,
        volume=ticker.volume or None,
        timestamp=str(ticker.time) if ticker.time else None
    )


@mcp.tool()
async def get_historical_data(
    symbol: str, 
    duration: str = "1 D",
    bar_size: str = "1 hour",
    exchange: str = "SMART"
) -> List[HistoricalBar]:
    """
    Get historical stock data
    
    Args:
        symbol: Stock symbol
        duration: Duration (e.g., '1 D', '1 W', '1 M')
        bar_size: Bar size (e.g., '1 min', '1 hour', '1 day')
        exchange: Exchange (default: SMART)
    """
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True
    )
    
    result = []
    for bar in bars:
        result.append(HistoricalBar(
            date=str(bar.date),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume
        ))
    
    return result


@mcp.tool()
async def get_option_chain(symbol: str, exchange: str = "SMART") -> List[OptionChain]:
    """
    Get option chain for a stock
    
    Args:
        symbol: Stock symbol
        exchange: Exchange (default: SMART)
    """
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    chains = ib.reqSecDefOptParams(
        contract.symbol, '', contract.secType, contract.conId
    )
    
    result = []
    if chains:
        for chain in chains:
            result.append(OptionChain(
                exchange=chain.exchange,
                strikes=sorted(list(chain.strikes)),
                expirations=sorted([str(exp) for exp in chain.expirations]),
                multiplier=str(chain.multiplier)
            ))
    
    return result


@mcp.tool()
async def place_limit_order(
    symbol: str,
    action: str,
    quantity: float,
    limit_price: float,
    exchange: str = "SMART"
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
    if READONLY:
        raise ValueError("Order placement is disabled in READONLY mode")
    
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = LimitOrder(action, quantity, limit_price)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)  # Wait for order to be submitted
    
    return OrderResult(
        order_id=trade.order.orderId,
        status=trade.orderStatus.status,
        symbol=symbol,
        action=action,
        quantity=quantity,
        limit_price=limit_price
    )


@mcp.tool()
async def place_market_order(
    symbol: str,
    action: str,
    quantity: float,
    exchange: str = "SMART"
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
    if READONLY:
        raise ValueError("Order placement is disabled in READONLY mode")
    
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = MarketOrder(action, quantity)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)
    
    return OrderResult(
        order_id=trade.order.orderId,
        status=trade.orderStatus.status,
        symbol=symbol,
        action=action,
        quantity=quantity
    )


@mcp.tool()
async def place_stop_order(
    symbol: str,
    action: str,
    quantity: float,
    stop_price: float,
    exchange: str = "SMART"
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
    if READONLY:
        raise ValueError("Order placement is disabled in READONLY mode")
    
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = StopOrder(action, quantity, stop_price)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)
    
    return OrderResult(
        order_id=trade.order.orderId,
        status=trade.orderStatus.status,
        symbol=symbol,
        action=action,
        quantity=quantity,
        stop_price=stop_price
    )


if __name__ == "__main__":
    logger.info(f"Starting IBKR MCP Server in {'READONLY' if READONLY else 'READ/WRITE'} mode")
    mcp.run(transport="http", host="0.0.0.0", port=SERVER_PORT)

