<<<<<<< HEAD
# Bittensor 子网评估采集器（首版骨架）

该项目按计划实现了首版命令行骨架：


## 快速开始

```bash
pip install -r requirements.txt
python run.py --config config/default.json
```

Windows 下也可以直接双击 [run_collector.bat](run_collector.bat) 运行。该脚本会自动检查 Python、按需安装依赖，并在结束后暂停显示结果。

## 常用参数

```bash
python run.py \
  --config config/default.json \
  --netuids 1,8,18,32,42 \
  --income-mode p30 \
  --output data/output/first_run.xlsx
```

## 说明

=======
# MyBittensor
none
>>>>>>> 1d81ddde8ed547f393f79322168357137b84ef97
# Bittensor 子网评估采集器（首版骨架）

该项目按计划实现了首版命令行骨架：

- 配置驱动的样本子网列表
- TAO.app / TAO Stats 拉取入口
- 官网/GitHub/Discord 的补充采集接口
- 统一数据模型与指标计算（中位收益/P30、Gini、HHI）
- Excel 多工作表导出（主表、原始证据、字段说明）

## 快速开始

```bash
pip install -r requirements.txt
python run.py --config config/default.json
```

Windows 下也可以直接双击 [run_collector.bat](run_collector.bat) 运行。该脚本会自动检查 Python、按需安装依赖，并在结束后暂停显示结果。

## 常用参数

```bash
python run.py \
  --config config/default.json \
  --netuids 1,8,18,32,42 \
  --income-mode p30 \
  --output data/output/first_run.xlsx
```

## 说明

- 首版优先保证流程可重复：自动抓结构化字段，定性字段留 evidence 与 manual_review_needed。
- 若某来源不可用，流程会继续并在证据表记录失败原因，不会中断整表。
