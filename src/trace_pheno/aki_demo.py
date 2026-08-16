"""Synthetic-only AKI example demonstrating reuse of time-window evidence."""

from __future__ import annotations


def creatinine_rule(values_mg_dl: list[float], times_h: list[float]) -> str:
    for i, current in enumerate(values_mg_dl):
        for j in range(i):
            if 0 <= times_h[i] - times_h[j] <= 48 and current - values_mg_dl[j] >= 0.3:
                return "delta_48h"
    baseline = values_mg_dl[0] if values_mg_dl else None
    if baseline and any(t <= 168 and value / baseline >= 1.5 for value, t in zip(values_mg_dl, times_h)):
        return "ratio_7d"
    return "negative"


def urine_rule(hourly_ml: list[float], weight_kg: float | None) -> str:
    if not weight_kg or weight_kg <= 0:
        return "missing_normalizer"
    if len(hourly_ml) < 6:
        return "insufficient_duration"
    for start in range(len(hourly_ml) - 5):
        rate = sum(hourly_ml[start : start + 6]) / 6 / weight_kg
        if rate < 0.5:
            return "urine_6h"
    return "negative"

