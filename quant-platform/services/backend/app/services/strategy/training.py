from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from ...core.config import get_settings
from .features import build_feature_frame, load_ohlcv_csv
from .model import ModelMetadata, StrategyModel, strategy_model


class TrainingDataMissing(RuntimeError):
    """Raised when the requested historical dataset cannot be located."""


def _resolve_dataset_path(override: str | None) -> Path:
    settings = get_settings()
    if override:
        candidate = Path(override)
    elif settings.historical_csv_path:
        candidate = settings.historical_csv_path
    else:
        raise TrainingDataMissing(
            "No historical CSV configured. Set HISTORICAL_CSV_PATH or provide dataset_path.",
        )

    if not candidate.exists():
        raise TrainingDataMissing(f"Historical dataset not found at {candidate}")
    return candidate


def train_random_forest(
    symbol: str,
    timeframe: str,
    dataset_path: str | None = None,
) -> ModelMetadata:
    csv_path = _resolve_dataset_path(dataset_path)
    df = load_ohlcv_csv(csv_path)

    if "symbol" in df.columns:
        df = df[df["symbol"] == symbol]
        if df.empty:
            raise TrainingDataMissing(f"Dataset does not contain symbol {symbol}")

    X, y, _ = build_feature_frame(df)
    if len(X) < 100:
        raise TrainingDataMissing("Not enough samples to train the model (need >= 100)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    pipeline = StrategyModel.create_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred)) if len(y_test) > 0 else None

    metadata = ModelMetadata(
        version=f"rf-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        trained_on=str(csv_path),
        samples=len(X_train),
        timeframe=timeframe,
        accuracy=accuracy,
        trained_at=datetime.utcnow().isoformat(),
    )

    strategy_model.replace_pipeline(pipeline, metadata)
    return metadata


def run_backtest(
    lookback_days: int,
    symbol: str,
    timeframe: str,
    dataset_path: str | None = None,
) -> dict[str, float | int]:
    csv_path = _resolve_dataset_path(dataset_path)
    df = load_ohlcv_csv(csv_path)

    if "symbol" in df.columns:
        df = df[df["symbol"] == symbol]
    if df.empty:
        raise TrainingDataMissing(f"No data available for symbol {symbol}")

    if lookback_days:
        window_start = df.index.max() - pd.Timedelta(days=lookback_days)
        df = df[df.index >= window_start]
    if df.empty:
        raise TrainingDataMissing("No data left after applying lookback window")

    X, _, future_returns = build_feature_frame(df)
    if X.empty:
        raise TrainingDataMissing("Insufficient candles to build features")

    if strategy_model.pipeline is None:
        strategy_model.load()
    assert strategy_model.pipeline is not None

    proba = strategy_model.pipeline.predict_proba(X)
    preds = (proba[:, 1] >= 0.5).astype(int)
    positions = np.where(preds == 1, 1, -1)

    aligned_returns = future_returns.loc[X.index].fillna(0.0)
    strat_returns = aligned_returns.values * positions
    trades = len(strat_returns)
    if trades == 0:
        raise TrainingDataMissing("Backtest produced zero trades")

    cum_returns = np.cumsum(strat_returns)
    equity_curve = (1 + strat_returns).cumprod()
    rolling_max = np.maximum.accumulate(equity_curve)
    drawdowns = (rolling_max - equity_curve) / rolling_max
    max_drawdown = float(np.max(drawdowns)) if trades > 0 else 0.0

    mean = np.mean(strat_returns)
    std = np.std(strat_returns)
    sharpe = float(np.sqrt(365) * mean / std) if std > 0 else 0.0
    win_rate = float((strat_returns > 0).sum() / trades)

    return {
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "trades": trades,
    }
