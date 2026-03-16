from fastapi import APIRouter, HTTPException, status

from ..schemas.strategy import (
    BacktestRequest,
    BacktestResponse,
    SignalRequest,
    SignalResponse,
    TrainRequest,
    TrainResponse,
)
from ...services.strategy.model import strategy_model
from ...services.strategy.training import (
    TrainingDataMissing,
    run_backtest,
    train_random_forest,
)
from ...notifications import send_telegram_alert

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post("/signal", response_model=SignalResponse, summary="Run AI inference on latest features")
async def generate_signal(payload: SignalRequest) -> SignalResponse:
    try:
        features = [payload.price, payload.rsi, payload.macd, payload.bollinger_band_width]
        result = strategy_model.predict(features)
    except Exception as exc:  # pragma: no cover - resilience
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to run strategy model: {exc}",
        ) from exc

    reason = result.get("metadata", {}).get("version", "model")
    return SignalResponse(
        direction=result["direction"],
        confidence=result["confidence"],
        reason=f"RandomForest {reason}",
    )


@router.post("/train", response_model=TrainResponse, summary="Train RandomForest model")
async def train_strategy(payload: TrainRequest) -> TrainResponse:
    try:
        metadata = train_random_forest(
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            dataset_path=payload.dataset_path,
        )
    except TrainingDataMissing as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - resilience
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {exc}",
        ) from exc

    response = TrainResponse(
        version=metadata.version,
        samples=metadata.samples,
        accuracy=metadata.accuracy,
        trained_at=metadata.trained_at or "",
    )
    await send_telegram_alert(
        f"🤖 Modèle {metadata.version} entraîné ({metadata.samples} échantillons, accuracy {metadata.accuracy or 'n/a'})",
    )
    return response


@router.post("/backtest", response_model=BacktestResponse, summary="Trigger historical backtest")
async def execute_backtest(payload: BacktestRequest) -> BacktestResponse:
    try:
        stats = run_backtest(
            lookback_days=payload.lookback_days,
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            dataset_path=payload.dataset_path,
        )
    except TrainingDataMissing as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - resilience
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {exc}",
        ) from exc

    response = BacktestResponse(**stats)
    await send_telegram_alert(
        "📊 Backtest: "
        f"Sharpe {response.sharpe_ratio:.2f} • Win rate {response.win_rate:.2%} • Trades {response.trades}"
    )
    return response
