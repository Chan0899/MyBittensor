from __future__ import annotations

from math import fsum

from bittensor_collector.config import ThresholdConfig
from bittensor_collector.models import SubnetRecord


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    idx = int((len(sorted_values) - 1) * q)
    return sorted_values[idx]


def middle_income(values: list[float], mode: str) -> float | None:
    if not values:
        return None
    if mode == "p30":
        return percentile(values, 0.30)
    return percentile(values, 0.50)


def compute_gini(values: list[float]) -> float | None:
    filtered = [v for v in values if v >= 0]
    if not filtered:
        return None
    sorted_values = sorted(filtered)
    n = len(sorted_values)
    total = fsum(sorted_values)
    if total == 0:
        return 0.0

    cum = 0.0
    for i, value in enumerate(sorted_values, start=1):
        cum += i * value
    return (2 * cum) / (n * total) - (n + 1) / n


def compute_hhi(values: list[float]) -> float | None:
    filtered = [v for v in values if v >= 0]
    total = fsum(filtered)
    if total <= 0:
        return None
    shares = [(v / total) for v in filtered]
    return fsum([s * s for s in shares])


def build_preliminary_conclusion(record: SubnetRecord, thresholds: ThresholdConfig) -> str:
    notes: list[str] = []

    if record.gini is not None and record.gini >= thresholds.high_gini:
        notes.append("集中度高(Gini偏高)")

    if record.hhi is not None and record.hhi >= thresholds.high_hhi:
        notes.append("市场份额过度集中(HHI偏高)")

    if (
        record.registration_fee_tao is not None
        and record.registration_fee_tao >= thresholds.high_registration_fee_tao
        and record.middle_daily_income_tao is not None
        and record.middle_daily_income_tao <= thresholds.low_middle_income_tao
    ):
        notes.append("注册费高且中游收益偏低")

    if record.validator_count is not None and record.validator_count < thresholds.min_validators:
        notes.append("验证者数量不足")

    if record.manual_review_needed:
        notes.append("存在待人工复核字段")

    return "；".join(notes) if notes else "结构化指标初步正常，建议结合定性证据复核"
