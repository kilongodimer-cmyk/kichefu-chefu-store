from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path("model_artifacts/latest_model.joblib")


@dataclass
class ModelMetadata:
    version: str
    trained_on: str
    samples: int
    timeframe: str | None = None
    accuracy: float | None = None
    trained_at: str | None = None


class StrategyModel:
    def __init__(self) -> None:
        self.pipeline: Pipeline | None = None
        self.metadata: ModelMetadata | None = None

    def load(self) -> None:
        if MODEL_PATH.exists():
            artifact = joblib.load(MODEL_PATH)
            self.pipeline = artifact["pipeline"]
            metadata = artifact.get("metadata")
            if isinstance(metadata, dict):
                self.metadata = ModelMetadata(**metadata)
            else:
                self.metadata = metadata
        else:
            self.pipeline = self.create_pipeline()
            self.metadata = ModelMetadata(
                version="dev",
                trained_on="synthetic",
                samples=0,
                timeframe=None,
                accuracy=None,
                trained_at=datetime.utcnow().isoformat(),
            )

    def predict(self, features: list[float]) -> dict[str, Any]:
        if self.pipeline is None:
            self.load()
        assert self.pipeline is not None
        arr = np.array([features])
        proba = self.pipeline.predict_proba(arr)[0]
        direction = "LONG" if proba[1] >= 0.5 else "SHORT"
        confidence = float(max(proba))
        return {
            "direction": direction,
            "confidence": confidence,
            "metadata": self.metadata.__dict__ if self.metadata else None,
        }

    @staticmethod
    def create_pipeline() -> Pipeline:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(n_estimators=200, random_state=42)),
            ]
        )

    def replace_pipeline(self, pipeline: Pipeline, metadata: ModelMetadata) -> None:
        self.pipeline = pipeline
        self.metadata = metadata
        self._persist()

    def _persist(self) -> None:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "metadata": self.metadata.__dict__}, MODEL_PATH)


strategy_model = StrategyModel()
