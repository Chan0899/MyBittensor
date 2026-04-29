from __future__ import annotations

import argparse
import shutil
import sys

from bittensor_collector.clients.tao_app import TaoAppClient
from bittensor_collector.clients.tao_stats import TaoStatsClient
from bittensor_collector.collectors.supplemental import SupplementalCollector
from bittensor_collector.config import AppConfig
from bittensor_collector.excel_exporter import export_excel
from bittensor_collector.pipeline import CollectorPipeline
from bittensor_collector.utils.http_client import HttpClient


def render_progress(current: int, total: int, message: str) -> None:
    total = max(total, 1)
    current = max(0, min(current, total))
    percent = current / total
    terminal_width = shutil.get_terminal_size(fallback=(80, 20)).columns
    reserved_width = len(message) + 16
    bar_width = max(10, min(40, terminal_width - reserved_width))
    filled = int(bar_width * percent)
    bar = "#" * filled + "-" * (bar_width - filled)
    line = f"[{bar}] {current}/{total} {percent:>6.1%} {message}"
    sys.stdout.write("\r" + line.ljust(terminal_width - 1))
    sys.stdout.flush()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bittensor 子网评估采集器")
    parser.add_argument("--config", default="config/default.json", help="配置文件路径")
    parser.add_argument("--netuids", default="", help="覆盖配置中的netuid列表，如 1,8,18")
    parser.add_argument("--income-mode", choices=["median", "p30"], default="", help="中游收益口径")
    parser.add_argument("--output", default="", help="Excel输出路径")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.load(args.config)

    if args.netuids:
        config.netuids = [int(x.strip()) for x in args.netuids.split(",") if x.strip()]
    if args.income_mode:
        config.runtime.income_mode = args.income_mode
    if args.output:
        config.paths.output_path = args.output

    config.ensure_paths()

    http_client = HttpClient(
        timeout_sec=config.runtime.request_timeout_sec,
        max_retries=config.runtime.max_retries,
        min_interval_sec=config.runtime.min_interval_sec,
        cache_dir=config.paths.cache_dir,
    )
    tao_app = TaoAppClient(config.sources.tao_app_base_url, http_client)
    tao_stats = TaoStatsClient(
        config.sources.tao_stats_base_url,
        http_client,
        api_token=config.sources.tao_stats_api,
    )
    supplemental = SupplementalCollector(config.sources.github_api_base_url, http_client)

    pipeline = CollectorPipeline(config, tao_app, tao_stats, supplemental)
    total_steps = max(len(config.netuids) + 1, 1)
    render_progress(0, total_steps, "准备开始")
    records, evidence_items = pipeline.run(
        progress_callback=lambda current, total, message: render_progress(
            current,
            max(total_steps - 1, 1),
            message,
        )
    )

    render_progress(total_steps - 1, total_steps, "正在导出 Excel")
    export_excel(records, evidence_items, config.paths.output_path)
    render_progress(total_steps, total_steps, "完成")
    print()
    print(f"Done. Records={len(records)}, evidence={len(evidence_items)}")
    print(f"Excel: {config.paths.output_path}")


if __name__ == "__main__":
    main()
