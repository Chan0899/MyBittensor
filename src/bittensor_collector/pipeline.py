from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from bittensor_collector.clients.tao_app import TaoAppClient
from bittensor_collector.clients.tao_stats import TaoStatsClient
from bittensor_collector.collectors.supplemental import SupplementalCollector
from bittensor_collector.config import AppConfig
from bittensor_collector.metrics import (
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
        tao_app: TaoAppClient,
        tao_stats: TaoStatsClient,
        supplemental: SupplementalCollector,
    ) -> None:
        self.config = config
        self.tao_app = tao_app
        self.tao_stats = tao_stats
        self.supplemental = supplemental

    def run(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[list[SubnetRecord], list[EvidenceItem]]:
        records: list[SubnetRecord] = []
        evidence_items: list[EvidenceItem] = []
        total = len(self.config.netuids)

        for index, netuid in enumerate(self.config.netuids, start=1):
            if progress_callback:
                progress_callback(index - 1, total, f"采集中 netuid={netuid}")

            snapshot_time = datetime.now(timezone.utc).isoformat()
            record = SubnetRecord(netuid=netuid, snapshot_time=snapshot_time)

            self._collect_from_tao_app(record, evidence_items)
            self._collect_from_tao_stats(record, evidence_items)
            self._collect_supplemental(record, evidence_items)

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

        return records, evidence_items

    def _collect_from_tao_app(self, record: SubnetRecord, evidence_items: list[EvidenceItem]) -> None:
        try:
            overview = self.tao_app.fetch_subnet_overview(record.netuid)
            metagraph = self.tao_app.fetch_metagraph(record.netuid)
            validators = self.tao_app.fetch_validators(record.netuid)

            record.subnet_name = _pick(overview, ["name", "subnet_name"], "")
            record.registration_fee_tao = _pick(
                overview,
                ["registration_fee_tao", "registration_cost", "burn"],
            )
            record.immunity_period_blocks = _pick(
                overview,
                ["immunity_period", "immunity_period_blocks"],
            )
            record.total_stake_tao = _pick(
                overview,
                ["total_stake_tao", "total_stake"],
            )

            income_dist = _pick(
                metagraph,
                ["miner_income_distribution", "miner_rewards", "miner_emissions"],
                [],
            )
            if isinstance(income_dist, list):
                record.miner_income_distribution = [
                    float(x) for x in income_dist if isinstance(x, (int, float))
                ]

            record.miner_count = _pick(metagraph, ["miner_count", "n_miners"]) or len(
                record.miner_income_distribution
            )
            record.validator_count = _pick(validators, ["validator_count", "n_validators"])

            record.gini = _pick(metagraph, ["gini"])
            record.hhi = _pick(metagraph, ["hhi"])

            evidence_items.append(
                EvidenceItem(
                    netuid=record.netuid,
                    source="tao_app",
                    field_name="overview/metagraph/validators",
                    source_url=f"{self.config.sources.tao_app_base_url}/subnets/{record.netuid}",
                    raw_text="TAO.app API data collected",
                )
            )
        except Exception as exc:  # noqa: BLE001
            record.manual_review_needed = True
            evidence_items.append(
                EvidenceItem(
                    netuid=record.netuid,
                    source="tao_app",
                    field_name="api_error",
                    source_url=self.config.sources.tao_app_base_url,
                    raw_text=str(exc),
                    manual_review_needed=True,
                )
            )

    def _collect_from_tao_stats(self, record: SubnetRecord, evidence_items: list[EvidenceItem]) -> None:
        try:
            detail = self.tao_stats.fetch_subnet_detail(record.netuid)
            record.subnet_name = record.subnet_name or _pick(detail, ["subnet_name"], "")
            record.domain = record.domain or _pick(detail, ["domain", "category"], "")
            record.registration_fee_tao = record.registration_fee_tao or _pick(
                detail,
                ["registration_fee_tao"],
            )
            record.hardware_requirement = _pick(
                detail,
                ["hardware_requirement", "hardware", "miner_hardware"],
                record.hardware_requirement,
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
            if not record.validator_quality_summary and _pick(detail, ["github_repo"]):
                record.validator_quality_summary = f"GitHub repo={detail['github_repo']}"
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

    def _collect_supplemental(self, record: SubnetRecord, evidence_items: list[EvidenceItem]) -> None:
        netuid_key = str(record.netuid)

        project_url = self.config.supplemental.project_urls.get(netuid_key)
        if project_url:
            try:
                page_info = self.supplemental.collect_project_page(project_url)
                if not record.domain:
                    record.domain = page_info.get("title", "")
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="project_page",
                        field_name="title/description",
                        source_url=project_url,
                        raw_text=page_info.get("description", ""),
                        manual_review_needed=True,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                record.manual_review_needed = True
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="project_page",
                        field_name="collect_error",
                        source_url=project_url,
                        raw_text=str(exc),
                        manual_review_needed=True,
                    )
                )

        repo_url = self.config.supplemental.github_repos.get(netuid_key)
        if repo_url:
            try:
                gh = self.supplemental.collect_github_summary(repo_url)
                record.validator_quality_summary = (
                    f"GitHub stars={gh.get('stargazers_count')}, pushed_at={gh.get('pushed_at')}"
                )
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="github",
                        field_name="repo_activity",
                        source_url=repo_url,
                        raw_text=str(gh),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                record.manual_review_needed = True
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="github",
                        field_name="collect_error",
                        source_url=repo_url,
                        raw_text=str(exc),
                        manual_review_needed=True,
                    )
                )

        if self.config.runtime.enable_discord:
            invite = self.config.supplemental.discord_invites.get(netuid_key)
            if invite:
                discord_info = self.supplemental.collect_discord_public_info(invite)
                record.community_feedback_summary = discord_info.get("note", "")
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="discord",
                        field_name="public_info",
                        source_url=invite,
                        raw_text=str(discord_info),
                        manual_review_needed=True,
                    )
                )
            else:
                record.manual_review_needed = True
                evidence_items.append(
                    EvidenceItem(
                        netuid=record.netuid,
                        source="discord",
                        field_name="missing_invite",
                        source_url="",
                        raw_text="Discord未配置invite链接",
                        manual_review_needed=True,
                    )
                )

        evidence_urls = [item.source_url for item in evidence_items if item.netuid == record.netuid and item.source_url]
        record.evidence_links = "\n".join(dict.fromkeys(evidence_urls))

        if not record.business_model_summary or not record.community_feedback_summary:
            record.manual_review_needed = True
