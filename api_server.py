"""
FastAPI REST API Server for CS:GO Trading Bot
Provides endpoints for Android mobile application
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import asyncio
from pathlib import Path
import secrets

# Import bot modules
from csgo_trading_bot import TradingBot, PriceAnalyzer
from config import Config
from logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="CS:GO Trading Bot API",
    description="REST API for CS:GO market analysis and trading recommendations",
    version="1.0.0"
)

# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Android app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global instances
config = Config()
logger = setup_logger(__name__)
trading_bot = None
price_analyzer = None

# Simple token storage (in production use proper auth like JWT)
VALID_TOKENS = set()


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class TokenResponse(BaseModel):
    """API token response"""
    token: str
    expires_in: int = Field(default=86400, description="Token validity in seconds")


class ItemPriceRequest(BaseModel):
    """Request for item price data"""
    item_name: str = Field(..., description="CS:GO item name")
    days: int = Field(default=30, ge=1, le=365, description="Number of days of history")


class ItemPriceResponse(BaseModel):
    """Item price data response"""
    item_name: str
    current_price: Optional[float]
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    data_points: int
    timestamp: str


class RecommendationRequest(BaseModel):
    """Request for trading recommendation"""
    item_name: str = Field(..., description="CS:GO item name")


class RecommendationResponse(BaseModel):
    """Trading recommendation response"""
    item: str
    recommendation: str  # BUY, SELL, HOLD
    confidence: float
    current_price: Optional[float]
    predicted_price: Optional[float]
    trend: Optional[str]
    reasons: List[str]
    timestamp: str


class MarketDataRequest(BaseModel):
    """Request to collect market data"""
    items: List[str] = Field(..., description="List of items to collect data for")
    force_update: bool = Field(default=False, description="Force fresh data collection")


class MarketDataResponse(BaseModel):
    """Market data collection response"""
    status: str
    items_processed: int
    success_count: int
    fail_count: int
    timestamp: str


class OpportunityResponse(BaseModel):
    """Trading opportunity response"""
    item: str
    confidence: float
    recommendation: str
    current_price: Optional[float]
    predicted_price: Optional[float]
    potential_profit: Optional[float]
    potential_percent: Optional[float]
    data_points: Optional[int]


class BacktestRequest(BaseModel):
    """Backtest request"""
    items: List[str]
    days: int = Field(default=30, ge=1, le=365)
    initial_balance: float = Field(default=100.0, gt=0)


class BacktestResponse(BaseModel):
    """Backtest results"""
    initial_balance: float
    final_value: float
    profit_loss: float
    roi: float
    total_trades: int
    win_rate: float
    timestamp: str


# ============================================================================
# Authentication
# ============================================================================

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API token"""
    token = credentials.credentials
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize bot components on startup"""
    global trading_bot, price_analyzer

    logger.info("🚀 Starting CS:GO Trading Bot API Server")

    try:
        # Initialize components
        trading_bot = TradingBot(config)
        price_analyzer = PriceAnalyzer(trading_bot.db_path, config)

        logger.info("✅ Bot components initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_bot, price_analyzer

    logger.info("🛑 Shutting down CS:GO Trading Bot API Server")

    if price_analyzer:
        price_analyzer.close()
    if trading_bot:
        trading_bot.__exit__(None, None, None)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CS:GO Trading Bot API",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_initialized": trading_bot is not None,
        "analyzer_initialized": price_analyzer is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/auth/token", response_model=TokenResponse)
async def get_token():
    """
    Get API access token
    In production, this would require username/password authentication
    """
    token = generate_token()
    VALID_TOKENS.add(token)

    return TokenResponse(token=token, expires_in=86400)


# ============================================================================
# Market Data Endpoints
# ============================================================================

@app.post("/api/market/collect", response_model=MarketDataResponse)
async def collect_market_data(
    request: MarketDataRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    Collect market data for specified items
    Runs in background to avoid timeout
    """
    if not trading_bot:
        raise HTTPException(status_code=503, detail="Trading bot not initialized")

    # Run data collection in background
    async def collect_data():
        success = 0
        fail = 0
        for item in request.items:
            try:
                listings = trading_bot.parser.get_item_listings(item, limit=20)
                if listings:
                    for listing in listings:
                        trading_bot.save_item_data(listing)
                    success += 1
                else:
                    fail += 1
            except Exception as e:
                logger.error(f"Error collecting data for {item}: {e}")
                fail += 1

        logger.info(f"Data collection complete: {success} success, {fail} failed")

    background_tasks.add_task(collect_data)

    return MarketDataResponse(
        status="started",
        items_processed=len(request.items),
        success_count=0,  # Will be updated in background
        fail_count=0,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/market/price", response_model=ItemPriceResponse)
async def get_item_price(
    request: ItemPriceRequest,
    token: str = Depends(verify_token)
):
    """Get price data for a specific item"""
    if not price_analyzer:
        raise HTTPException(status_code=503, detail="Price analyzer not initialized")

    try:
        df = price_analyzer.get_item_dataframe(request.item_name, request.days)

        if df is None or len(df) == 0:
            return ItemPriceResponse(
                item_name=request.item_name,
                current_price=None,
                avg_price=None,
                min_price=None,
                max_price=None,
                data_points=0,
                timestamp=datetime.now().isoformat()
            )

        return ItemPriceResponse(
            item_name=request.item_name,
            current_price=float(df['price'].iloc[-1]),
            avg_price=float(df['price'].mean()),
            min_price=float(df['price'].min()),
            max_price=float(df['price'].max()),
            data_points=len(df),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting price for {request.item_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Trading Recommendation Endpoints
# ============================================================================

@app.post("/api/recommendations/item", response_model=RecommendationResponse)
async def get_item_recommendation(
    request: RecommendationRequest,
    token: str = Depends(verify_token)
):
    """Get trading recommendation for a specific item"""
    if not price_analyzer:
        raise HTTPException(status_code=503, detail="Price analyzer not initialized")

    try:
        rec = price_analyzer.get_buy_recommendation(request.item_name)

        if not rec:
            raise HTTPException(status_code=404, detail=f"No data available for {request.item_name}")

        return RecommendationResponse(
            item=request.item_name,
            recommendation=rec.get('recommendation', 'HOLD'),
            confidence=rec.get('confidence', 0),
            current_price=rec.get('current_price'),
            predicted_price=rec.get('predicted_price'),
            trend=rec.get('trend'),
            reasons=rec.get('reasons', []),
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation for {request.item_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    limit: int = 10,
    min_confidence: int = 50,
    token: str = Depends(verify_token)
):
    """Get top trading opportunities"""
    if not price_analyzer:
        raise HTTPException(status_code=503, detail="Price analyzer not initialized")

    try:
        # Get configured items
        items = config.get('items', [])
        if not items:
            raise HTTPException(status_code=404, detail="No items configured")

        opportunities = []

        for item in items:
            try:
                rec = price_analyzer.get_buy_recommendation(item)

                if not rec or rec.get('confidence', 0) < min_confidence:
                    continue

                if rec.get('recommendation') != 'BUY':
                    continue

                current = rec.get('current_price')
                predicted = rec.get('predicted_price')

                potential_profit = None
                potential_percent = None

                if predicted is not None and current is not None and current > 0:
                    potential_profit = predicted - current
                    potential_percent = (potential_profit / current) * 100

                opportunities.append(OpportunityResponse(
                    item=item,
                    confidence=rec['confidence'],
                    recommendation=rec['recommendation'],
                    current_price=current,
                    predicted_price=predicted,
                    potential_profit=potential_profit,
                    potential_percent=potential_percent,
                    data_points=rec.get('data_points')
                ))

            except Exception as e:
                logger.warning(f"Error processing {item}: {e}")
                continue

        # Sort by confidence
        opportunities.sort(key=lambda x: x.confidence, reverse=True)

        return opportunities[:limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================

@app.get("/api/stats/summary")
async def get_stats_summary(token: str = Depends(verify_token)):
    """Get overall statistics summary"""
    if not price_analyzer or not trading_bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        items = config.get('items', [])

        total_items = len(items)
        items_with_data = 0
        total_data_points = 0

        for item in items:
            df = price_analyzer.get_item_dataframe(item, 7)
            if df is not None and len(df) > 0:
                items_with_data += 1
                total_data_points += len(df)

        return {
            "total_items": total_items,
            "items_with_data": items_with_data,
            "total_data_points": total_data_points,
            "coverage_percent": (items_with_data / total_items * 100) if total_items > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Configuration Endpoints
# ============================================================================

@app.get("/api/config/items")
async def get_configured_items(token: str = Depends(verify_token)):
    """Get list of configured items"""
    items = config.get('items', [])
    return {
        "items": items,
        "count": len(items),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Main entry point
# ============================================================================

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
