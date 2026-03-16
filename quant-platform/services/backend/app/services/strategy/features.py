from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2


def load_ohlcv_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")

    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="ignore")
        df = df.sort_values("timestamp")
        df = df.set_index("timestamp")
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    candles = df.copy()
    close = candles["close"]

    candles["rsi"] = _rsi(close, RSI_PERIOD)
    macd, signal, hist = _macd(close)
    candles["macd"] = macd
    candles["macd_signal"] = signal
    candles["macd_hist"] = hist
    upper, lower = _bollinger(close)
    candles["bollinger_width"] = (upper - lower) / close
    candles["returns"] = close.pct_change()
    candles["future_return"] = close.pct_change().shift(-1)
    candles.dropna(inplace=True)
    return candles


def build_feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    enriched = compute_indicators(df)
    feature_cols = [
        "rsi",
        "macd",
        "macd_signal",
        "macd_hist",
        "bollinger_width",
        "returns",
        "volume",
    ]
    X = enriched[feature_cols]
    y = (enriched["future_return"] > 0).astype(int)
    future_returns = enriched["future_return"].loc[X.index]
    return X, y, future_returns


def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = series.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = series.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def _bollinger(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    middle = series.rolling(window=BOLLINGER_PERIOD).mean()
    std = series.rolling(window=BOLLINGER_PERIOD).std()
    upper = middle + BOLLINGER_STD * std
    lower = middle - BOLLINGER_STD * std
    return upper, lower
