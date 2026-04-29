from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvidenceItem:
    netuid: int
    source: str
    field_name: str
    source_url: str
    raw_text: str
    manual_review_needed: bool = False


@dataclass
class SubnetRecord:
    netuid: int
    snapshot_time: str
    subnet_name: str = ""
    domain: str = ""
    registration_fee_tao: Optional[float] = None
    hardware_requirement: str = ""
    middle_daily_income_tao: Optional[float] = None
    gini: Optional[float] = None
    hhi: Optional[float] = None
    miner_count: Optional[int] = None
    validator_count: Optional[int] = None
    total_stake_tao: Optional[float] = None
    immunity_period_blocks: Optional[int] = None
    validator_quality_summary: str = ""
    evidence_links: str = ""
    preliminary_conclusion: str = ""
    business_model_summary: str = ""
    community_feedback_summary: str = ""
    manual_review_needed: bool = False
    miner_income_distribution: list[float] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_main_row(self) -> dict:
        return {
            "子网ID": self.netuid,
            "子网名称": self.subnet_name,
            "领域": self.domain,
            "注册费(TAO)": self.registration_fee_tao,
            "硬件要求": self.hardware_requirement,
            "中游日收益(TAO)": self.middle_daily_income_tao,
            "Gini": self.gini,
            "HHI": self.hhi,
            "矿工数": self.miner_count,
            "验证者数": self.validator_count,
            "总质押量(TAO)": self.total_stake_tao,
            "免疫期(块)": self.immunity_period_blocks,
            "验证者质量摘要": self.validator_quality_summary,
            "证据链接": self.evidence_links,
            "商业模式摘要": self.business_model_summary,
            "社区反馈摘要": self.community_feedback_summary,
            "初步结论": self.preliminary_conclusion,
            "需人工复核": self.manual_review_needed,
            "快照时间": self.snapshot_time,
        }
