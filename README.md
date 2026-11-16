# 风光氢电混合储能微网实验框架

用同一套输入校验和输出格式复算已给定的购电功率序列，后续可通过求解器接口接入论文调度模型。

## 快速运行

需要 Python 3.11 或更新版本。运行和测试只使用 Python 标准库。在仓库根目录运行：

```bash
python -m unittest discover -s tests -v
python -m microgrid.cli --input examples/synthetic_import.csv --output results/peak.json
```

合成样例的峰值为 3.5 kW，出现两次。这组值只用于验证程序。JSON 记录输入文件 SHA-256、Python 版本、样本数、峰值及全部并列峰值的 UTC 时间。复算时保留输入原件与 Git 提交号，使用相同 Python 版本可验证输出字节一致。

可选安装方式为 `python -m pip install .`，安装后可用 `microgrid-peak` 代替 `python -m microgrid.cli`。

## 输入约定

- CSV 使用 UTF-8，可带 BOM。峰值计算要求 `timestamp` 和 `grid_import_kw`。时间戳使用带时区偏移的 ISO 8601，按实际时间严格递增。
- 功率列为有限、非负的 kW 值。`grid_import_kw` 表示从电网购入的功率。若原始数据记录带符号的净交换功率，先按其符号约定提取购电功率。
- 有可选的 `load_kw`、`wind_kw`、`solar_kw` 时同样校验功率。未来适配器可使用 `read_series(data, required=DISPATCH_COLUMNS)` 读取候选调度输入。
- 当前实现取输入样本的最大值。若论文峰值定义采用计费窗口平均功率，需先按已确认的窗口生成输入。调度模型接入时还需确认步长及缺口处理。

## 目录

| 路径 | 用途 |
| --- | --- |
| `microgrid/inputs.py` | 读取 CSV 并校验结构、时间和功率 |
| `microgrid/peak.py` | 计算最大购电功率并返回所有峰值时刻 |
| `microgrid/model.py` | 模型配置和求解器接口 |
| `microgrid/cli.py`、`microgrid/results.py` | 命令行及 JSON 导出 |
| `examples/` | 合成输入和待填写的模型配置 |
| `tests/` | 单元测试与端到端复算测试 |

## 接入论文模型

`examples/model.pending.json` 中三个区块均为 `null`，表示待核实。实现 `DispatchSolver.solve(series, parameters)` 时，由适配器验证各区块的具体字段、单位和取值范围，并返回求解状态、求解器版本及与输入时间对齐的购电功率序列。

| 待核实区块 | 接入前需要确认 |
| --- | --- |
| `hydrogen_conversion` | 电解槽与燃料电池转换关系、效率口径、能量或质量单位、储氢状态方程及边界 |
| `cost_budget` | 成本项、预算来源、币种、计价周期及预算约束表达式 |
| `dispatch_equations` | 电功率平衡、电池及储氢跨时段约束、初末状态、购售电边界、峰值定义及目标函数 |

有可行调度序列后，可复用 `measure_peak`。正式基准和对比实验使用同一时段和时间分辨率，并保留输入及配置摘要、求解器版本与设置、求解状态和结果。当前命令只测量给定序列的峰值。
