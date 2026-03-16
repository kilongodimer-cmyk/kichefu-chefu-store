from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
    price: float = Field(..., gt=0)
    rsi: float
    macd: float
    bollinger_band_width: float
    timestamp: str


class SignalResponse(BaseModel):
    direction: str
    confidence: float
    reason: str


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    lookback_days: int = Field(..., ge=30, le=365)
    dataset_path: str | None = Field(
        default=None,
        description="Optional override for the historical CSV path",
    )


class BacktestResponse(BaseModel):
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: int


class TrainRequest(BaseModel):
    symbol: str
    timeframe: str
    dataset_path: str | None = None


class TrainResponse(BaseModel):
    version: str
    samples: int
    accuracy: float | None
    trained_at: str
