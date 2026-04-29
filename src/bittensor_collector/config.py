from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RuntimeConfig:
    request_timeout_sec: int = 15
    max_retries: int = 3
    min_interval_sec: float = 0.35
    enable_discord: bool = False
    income_mode: str = "median"


@dataclass
class SourceConfig:
    tao_app_base_url: str = "https://api.tao.app"
    tao_stats_base_url: str = "https://taostats.io"
    tao_stats_api: str = ""
    github_api_base_url: str = "https://api.github.com"


@dataclass
class ThresholdConfig:
    high_gini: float = 0.75
    high_hhi: float = 0.25
    high_registration_fee_tao: float = 10.0
    low_middle_income_tao: float = 0.2
    min_validators: int = 16


@dataclass
class PathConfig:
    cache_dir: str = "data/cache"
    output_path: str = "data/output/subnet_assessment.xlsx"


@dataclass
class SupplementalConfig:
    github_repos: dict[str, str] = field(default_factory=dict)
    project_urls: dict[str, str] = field(default_factory=dict)
    discord_invites: dict[str, str] = field(default_factory=dict)


@dataclass
class AppConfig:
    netuids: list[int]
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    sources: SourceConfig = field(default_factory=SourceConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    supplemental: SupplementalConfig = field(default_factory=SupplementalConfig)

    @classmethod
    def load(cls, path: str | Path) -> "AppConfig":
        config_path = Path(path)
        payload = json.loads(config_path.read_text(encoding="utf-8"))

        return cls(
            netuids=payload.get("netuids", []),
            runtime=RuntimeConfig(**payload.get("runtime", {})),
            sources=SourceConfig(**payload.get("sources", {})),
            thresholds=ThresholdConfig(**payload.get("thresholds", {})),
            paths=PathConfig(**payload.get("paths", {})),
            supplemental=SupplementalConfig(**payload.get("supplemental", {})),
        )

    def ensure_paths(self) -> None:
        Path(self.paths.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.paths.output_path).parent.mkdir(parents=True, exist_ok=True)
