#!/usr/bin/env python3
"""
IBKR MCP Server
A Model Context Protocol server that provides IBKR trading capabilities.
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ib_async import IB, Stock, Option, Order, LimitOrder, MarketOrder, StopOrder
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IBKR connection settings from environment
IBKR_HOST = os.getenv("IBKR_HOST", "ib-gateway")
IBKR_PORT = int(os.getenv("IBKR_GATEWAY_PORT", "4002"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

# Global IB connection
ib = IB()


async def ensure_connected():
    """Ensure IB connection is active."""
    if not ib.isConnected():
        try:
            await ib.connectAsync(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
            logger.info(f"Connected to IB Gateway at {IBKR_HOST}:{IBKR_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to IB Gateway: {e}")
            raise


async def get_account_summary() -> Dict[str, Any]:
    """Get account summary including cash flow."""
    await ensure_connected()
    
    account_values = ib.accountValues()
    summary = {}
    
    for av in account_values:
        if av.tag in ['NetLiquidation', 'CashBalance', 'TotalCashValue', 
                      'BuyingPower', 'GrossPositionValue']:
            summary[av.tag] = {
                'value': av.value,
                'currency': av.currency,
                'account': av.account
            }
    
    return summary


async def get_positions() -> List[Dict[str, Any]]:
    """Get all current positions."""
    await ensure_connected()
    
    positions = ib.positions()
    result = []
    
    for pos in positions:
        result.append({
            'account': pos.account,
            'symbol': pos.contract.symbol,
            'secType': pos.contract.secType,
            'exchange': pos.contract.exchange,
            'position': pos.position,
            'avgCost': pos.avgCost,
            'marketPrice': pos.marketPrice,
            'marketValue': pos.marketValue,
            'unrealizedPNL': pos.unrealizedPNL,
            'realizedPNL': pos.realizedPNL
        })
    
    return result


async def get_orders() -> List[Dict[str, Any]]:
    """Get all orders."""
    await ensure_connected()
    
    trades = ib.trades()
    result = []
    
    for trade in trades:
        result.append({
            'orderId': trade.order.orderId,
            'symbol': trade.contract.symbol,
            'action': trade.order.action,
            'orderType': trade.order.orderType,
            'totalQuantity': trade.order.totalQuantity,
            'lmtPrice': trade.order.lmtPrice,
            'auxPrice': trade.order.auxPrice,
            'status': trade.orderStatus.status,
            'filled': trade.orderStatus.filled,
            'remaining': trade.orderStatus.remaining,
            'avgFillPrice': trade.orderStatus.avgFillPrice,
        })
    
    return result


async def get_stock_price(symbol: str, exchange: str = "SMART") -> Dict[str, Any]:
    """Get real-time stock price."""
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    ticker = ib.reqMktData(contract)
    await asyncio.sleep(2)  # Wait for data
    ib.cancelMktData(contract)
    
    return {
        'symbol': symbol,
        'bid': ticker.bid,
        'ask': ticker.ask,
        'last': ticker.last,
        'close': ticker.close,
        'volume': ticker.volume,
        'time': str(ticker.time)
    }


async def get_historical_data(
    symbol: str, 
    duration: str = "1 D",
    bar_size: str = "1 hour",
    exchange: str = "SMART"
) -> List[Dict[str, Any]]:
    """Get historical stock data."""
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
        result.append({
            'date': str(bar.date),
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
    
    return result


async def get_option_chain(
    symbol: str,
    exchange: str = "SMART"
) -> List[Dict[str, Any]]:
    """Get option chain for a stock."""
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    chains = ib.reqSecDefOptParams(
        contract.symbol, '', contract.secType, contract.conId
    )
    
    result = []
    if chains:
        for chain in chains:
            result.append({
                'exchange': chain.exchange,
                'strikes': list(chain.strikes),
                'expirations': [str(exp) for exp in chain.expirations],
                'multiplier': chain.multiplier
            })
    
    return result


async def place_limit_order(
    symbol: str,
    action: str,
    quantity: float,
    limit_price: float,
    exchange: str = "SMART"
) -> Dict[str, Any]:
    """Place a limit order."""
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = LimitOrder(action, quantity, limit_price)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)  # Wait for order to be submitted
    
    return {
        'orderId': trade.order.orderId,
        'status': trade.orderStatus.status,
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'limitPrice': limit_price
    }


async def place_market_order(
    symbol: str,
    action: str,
    quantity: float,
    exchange: str = "SMART"
) -> Dict[str, Any]:
    """Place a market order."""
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = MarketOrder(action, quantity)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)
    
    return {
        'orderId': trade.order.orderId,
        'status': trade.orderStatus.status,
        'symbol': symbol,
        'action': action,
        'quantity': quantity
    }


async def place_stop_order(
    symbol: str,
    action: str,
    quantity: float,
    stop_price: float,
    exchange: str = "SMART"
) -> Dict[str, Any]:
    """Place a stop order."""
    await ensure_connected()
    
    contract = Stock(symbol, exchange, 'USD')
    ib.qualifyContracts(contract)
    
    order = StopOrder(action, quantity, stop_price)
    trade = ib.placeOrder(contract, order)
    
    await asyncio.sleep(1)
    
    return {
        'orderId': trade.order.orderId,
        'status': trade.orderStatus.status,
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'stopPrice': stop_price
    }


# Create MCP server
app = Server("ibkr-mcp-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_account_summary",
            description="Get account summary including cash balance and net liquidation value",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_positions",
            description="Get all current positions in the account",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_orders",
            description="Get all orders (open and filled)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_stock_price",
            description="Get real-time stock price",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA)"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_historical_data",
            description="Get historical stock data",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Duration (e.g., '1 D', '1 W', '1 M')",
                        "default": "1 D"
                    },
                    "bar_size": {
                        "type": "string",
                        "description": "Bar size (e.g., '1 min', '1 hour', '1 day')",
                        "default": "1 hour"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_option_chain",
            description="Get option chain for a stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="place_limit_order",
            description="Place a limit order",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "action": {
                        "type": "string",
                        "description": "BUY or SELL",
                        "enum": ["BUY", "SELL"]
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Number of shares"
                    },
                    "limit_price": {
                        "type": "number",
                        "description": "Limit price"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol", "action", "quantity", "limit_price"]
            }
        ),
        Tool(
            name="place_market_order",
            description="Place a market order",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "action": {
                        "type": "string",
                        "description": "BUY or SELL",
                        "enum": ["BUY", "SELL"]
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Number of shares"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol", "action", "quantity"]
            }
        ),
        Tool(
            name="place_stop_order",
            description="Place a stop (stop-loss) order",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "action": {
                        "type": "string",
                        "description": "BUY or SELL",
                        "enum": ["BUY", "SELL"]
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Number of shares"
                    },
                    "stop_price": {
                        "type": "number",
                        "description": "Stop price"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (default: SMART)",
                        "default": "SMART"
                    }
                },
                "required": ["symbol", "action", "quantity", "stop_price"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_account_summary":
            result = await get_account_summary()
        elif name == "get_positions":
            result = await get_positions()
        elif name == "get_orders":
            result = await get_orders()
        elif name == "get_stock_price":
            result = await get_stock_price(
                arguments["symbol"],
                arguments.get("exchange", "SMART")
            )
        elif name == "get_historical_data":
            result = await get_historical_data(
                arguments["symbol"],
                arguments.get("duration", "1 D"),
                arguments.get("bar_size", "1 hour"),
                arguments.get("exchange", "SMART")
            )
        elif name == "get_option_chain":
            result = await get_option_chain(
                arguments["symbol"],
                arguments.get("exchange", "SMART")
            )
        elif name == "place_limit_order":
            result = await place_limit_order(
                arguments["symbol"],
                arguments["action"],
                arguments["quantity"],
                arguments["limit_price"],
                arguments.get("exchange", "SMART")
            )
        elif name == "place_market_order":
            result = await place_market_order(
                arguments["symbol"],
                arguments["action"],
                arguments["quantity"],
                arguments.get("exchange", "SMART")
            )
        elif name == "place_stop_order":
            result = await place_stop_order(
                arguments["symbol"],
                arguments["action"],
                arguments["quantity"],
                arguments["stop_price"],
                arguments.get("exchange", "SMART")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
