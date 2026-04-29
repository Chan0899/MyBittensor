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
    middle_daily_income_tao: Optional[float] = None
    gini: Optional[float] = None
    hhi: Optional[float] = None
    heat_score: Optional[float] = None
    miner_count: Optional[int] = None
    validator_count: Optional[int] = None
    total_stake_tao: Optional[float] = None
    immunity_period_blocks: Optional[int] = None
    preliminary_conclusion: str = ""
    business_model_summary: str = ""
    manual_review_needed: bool = False
    miner_income_distribution: list[float] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_main_row(self) -> dict:
        return {
            "子网ID": self.netuid,
            "子网名称": self.subnet_name,
            "领域": self.domain,
            "注册费(TAO)": self.registration_fee_tao,
            "中游日收益(TAO)": self.middle_daily_income_tao,
            "Gini": round(self.gini, 2) if self.gini is not None else None,
            "HHI": round(self.hhi, 2) if self.hhi is not None else None,
            "热度": round(self.heat_score, 2) if self.heat_score is not None else None,
            "矿工数": self.miner_count,
            "验证者数": self.validator_count,
            "总质押量(TAO)": self.total_stake_tao,
            "免疫期(块)": self.immunity_period_blocks,
            "商业模式摘要": self.business_model_summary,
            "初步结论": self.preliminary_conclusion,
            "需人工复核": self.manual_review_needed,
            "快照时间": self.snapshot_time,
        }
