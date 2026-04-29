from __future__ import annotations

import sys
from pathlib import Path

# 允许在未安装包的情况下直接运行 src 布局项目。
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bittensor_collector.cli import main


if __name__ == "__main__":
    main()
