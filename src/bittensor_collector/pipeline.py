from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from bittensor_collector.clients.tao_stats import TaoStatsClient
from bittensor_collector.config import AppConfig
from bittensor_collector.metrics import (
    apply_heat_scores,
    build_preliminary_conclusion,
    compute_gini,
    compute_hhi,
    middle_income,
)
from bittensor_collector.models import EvidenceItem, SubnetRecord


ProgressCallback = Callable[[int, int, str], None]


def _pick(data: dict, keys: list[str], default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


class CollectorPipeline:
    def __init__(
        self,
        config: AppConfig,
        tao_stats: TaoStatsClient,
    ) -> None:
        self.config = config
        self.tao_stats = tao_stats

    def resolve_netuids(self) -> list[int]:
        if self.config.netuids:
            return self.config.netuids
        return self.tao_stats.list_netuids()

    def run(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[list[SubnetRecord], list[EvidenceItem]]:
        records: list[SubnetRecord] = []
        evidence_items: list[EvidenceItem] = []
        netuids = self.resolve_netuids()
        total = len(netuids)

        for index, netuid in enumerate(netuids, start=1):
            if progress_callback:
                progress_callback(index - 1, total, f"采集中 netuid={netuid}")

            snapshot_time = datetime.now(timezone.utc).isoformat()
            record = SubnetRecord(netuid=netuid, snapshot_time=snapshot_time)

            self._collect_from_tao_stats(record, evidence_items)

            record.middle_daily_income_tao = middle_income(
                record.miner_income_distribution,
                self.config.runtime.income_mode,
            )
            if record.gini is None:
                record.gini = compute_gini(record.miner_income_distribution)
            if record.hhi is None:
                record.hhi = compute_hhi(record.miner_income_distribution)

            record.preliminary_conclusion = build_preliminary_conclusion(
                record, self.config.thresholds
            )
            records.append(record)

            if progress_callback:
                progress_callback(index, total, f"已完成 netuid={netuid}")

        apply_heat_scores(records)
        return records, evidence_items

    def _collect_from_tao_stats(self, record: SubnetRecord, evidence_items: list[EvidenceItem]) -> None:
        try:
            detail = self.tao_stats.fetch_subnet_detail(record.netuid)
            record.subnet_name = record.subnet_name or _pick(detail, ["subnet_name"], "")
            record.domain = record.domain or _pick(detail, ["domain", "category"], "")
            record.registration_fee_tao = record.registration_fee_tao or _pick(
                detail,
                ["registration_fee_tao"],
            )
            record.total_stake_tao = record.total_stake_tao or _pick(
                detail,
                ["total_stake_tao"],
            )
            record.immunity_period_blocks = record.immunity_period_blocks or _pick(
                detail,
                ["immunity_period_blocks"],
            )
            income_dist = _pick(detail, ["miner_income_distribution"], [])
            if isinstance(income_dist, list) and income_dist:
                record.miner_income_distribution = income_dist
            record.miner_count = record.miner_count or _pick(detail, ["miner_count"])
            record.validator_count = record.validator_count or _pick(detail, ["validator_count"])
            record.business_model_summary = _pick(
                detail,
                ["business_model", "business_model_summary"],
                record.business_model_summary,
            )
            evidence_items.append(
                EvidenceItem(
                    netuid=record.netuid,
                    source="tao_stats",
                    field_name="subnet_detail",
                    source_url=f"{self.config.sources.tao_stats_base_url}/api/subnet/latest/v1?netuid={record.netuid}",
                    raw_text="TAO Stats latest/identity/metagraph/pool collected",
                )
            )
        except Exception as exc:  # noqa: BLE001
            record.manual_review_needed = True
            evidence_items.append(
                EvidenceItem(
                    netuid=record.netuid,
                    source="tao_stats",
                    field_name="api_error",
                    source_url=self.config.sources.tao_stats_base_url,
                    raw_text=str(exc),
                    manual_review_needed=True,
                )
            )
