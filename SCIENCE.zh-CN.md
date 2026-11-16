# 通用分析与代码作图 · v0.3

[English](SCIENCE.md) | **简体中文**

本模块面向明确实验设计的长表数据，支持与 Prism 无关的组名、单位和领域。它计算统计结果，并生成真正的 Matplotlib 矢量对象。**它不会把代码图冒充为 Prism 原生项目，也不会仅凭一张表推断实验设计。**

## 从示例到自己的数据

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[science]'
.venv/bin/python demo_science.py --directory local/demo
.venv/bin/figureflow inspect local/demo/manufacturing.csv
.venv/bin/figureflow analyze local/demo/manufacturing.json --output-dir local/my-first-run
```

目录必须是新的。`demo_science.py` 创建 8 份完全合成的案例、输入表、显式配置和各自的输出，固定随机种子，不读取用户实验文件。复制最接近设计的配置到自己的任务目录，替换列映射、单位、实验单位 ID、组顺序、设计和方法，再运行 `analyze`。仅修改标题不等于适配一个新研究。

只用旧审计命令可 `pip install .`，无需科学计算依赖。运行完整测试或新分析命令需 `[science]`；安装阶段可能下载构建工具和依赖。

## 支持范围与方法

| design / method | 数据结构与最小条件 | 结果及绘图 |
|---|---|---|
| independent / welch_t | 两组、每组至少 2 个独立单位；全表 ID 唯一 | 双侧 Welch t，均值差 A−B、95% CI、df、P；原始散点与摘要 |
| paired / paired_t | 两条件，各至少 2 个相同 ID；每个 ID/条件恰好一条 | 按 ID 配对的双侧 t；均值差、95% CI、df、P；配对连线 |
| independent / anova | 至少两组，每组至少 2；独立、正态误差、等方差前提须审阅 | 普通单因素 ANOVA 总体 F/P；可选明确列出的 Welch 两两比较 + Holm 校正 |
| independent / kruskal | 至少两组、每组至少 5；独立单位 | Kruskal–Wallis 总体 H/P；不自动产生组对结论或括线 |
| independent / descriptive | 至少两组，每组至少 2 | 原始点与 mean/SD/median/quartiles；不计算 P |
| correlation / pearson | 至少 4 对独立、非恒定 x/y | Pearson r、双侧 P、Fisher 变换 95% CI；散点图 |
| correlation / spearman_permutation | 至少 4 对独立、非恒定 x/y；置换需可交换性 | Spearman rho、双侧置换 P；最多请求 9,999 次，seed=0，小样本可穷举；未实现 CI |
| contingency / fisher_exact | 完整 2×2 实际人数/次数表，非负整数、行列边际非零 | 双侧 Fisher P、样本 odds ratio；计数柱图；未实现 OR 的 CI |
| time_series / descriptive | 唯一数值时间或 YYYY-MM-DD，明确顺序 | 按时间排序连线；不计算趋势检验、跨时点 P 或因果结论 |

ANOVA/Kruskal 的总体 P 是上尾检验，不是任意一对的 P。t、相关和 Fisher 使用双侧检验。不同配置文件之间没有自动多重校正：若它们属于同一检验家族，需要另行声明和处理，不能将分文件运行当作避开多重比较的方法。

ANOVA 可选两两比较明确采用 Welch，**不是** Tukey/Dunnett，也不是根据总体 P 再挑选显著组。Holm 家族包含配置中全部组对，不筛掉 ns；报告同时保留原始和校正 P。组对 CI 目前是未校正 95% CI，不把它们称作同时置信区间。总体 ANOVA 假设不适用时，不能靠附加 Welch 组对来补救总体检验。

Pearson 的 P/CI 有其模型假设；软件不会用一次正态性检验替研究者选模型。Kruskal 是秩分布检验，在没有相同分布形状等前提时不能简单称为中位数检验。所有 n 均由实际参与分析的记录/配对确定，但声明 ID 唯一不证明真实独立性。

## 配置合同

```json
{
  "schema_version": 1,
  "source": {"path": "measurements.csv"},
  "design": "independent",
  "method": "welch_t",
  "columns": {"id": "part_serial", "group": "process", "value": "diameter_mm"},
  "group_order": ["Lathe A", "Lathe B"],
  "missing": "error",
  "design_confirmed": true,
  "assumptions": "Different parts are independent units; review normal-error assumptions for this small-sample comparison.",
  "title": "Manufacturing tolerances",
  "x_label": "Process",
  "y_label": "Diameter",
  "unit": "mm",
  "style": {"font": "DejaVu Sans", "width": 7, "height": 5, "summary": "mean_sd", "show_significance": true}
}
```

- 必填字段见示例；未知键、重复 JSON 键、错拼方法、未确认设计都会报错，绝不回退为另一个检验。
- `source.path` 相对配置文件目录。CSV/TSV 是 UTF-8，可带 BOM；XLSX 多工作表必须用 `source.sheet` 明确指定。拒绝公式单元格，避免读取过期计算缓存。标题必须是唯一非空文本。
- `columns` 指定源列名，允许不同命名，但角色必须完整且互不重复。分组为 `id/group/value`；相关/时间为 `id/x/y`；列联表为 `row/column/count`。无隐式重命名、单位换算、长宽表重塑或技术重复聚合。
- `group_order` 必须与实际观察组集合一致；不能靠漏写组名过滤数据。独立组 ID 全表唯一；配对 ID 允许跨条件重复，但同条件不得重复。数值相等不去重。
- `missing=error` 默认由配置明确写出；`drop` 只删除映射字段中有空值的行，记录原始行号和原因。不插补、不删异常值、不自动删不完整配对；配对不齐会拒绝分析。空字符串/Excel 空单元格为空，`NA`、`NaN`、无穷和带千分位逗号的文本不悄悄转换。
- 列联表必须声明 `count_basis=observed_counts`；计数必须是小于 2^53 的非负整数。**50/50 既可能是计数也可能是百分比，软件无法从数字本身判定。** 不能从百分比猜总 n；输入来源由操作者核实。
- 时间序列必须声明 `time_kind=numeric` 或 `iso_date`；日期不接受含时分秒、重复坐标或非 ISO 格式。
- ANOVA 组对需要 `contrasts=[{"a":"Baseline","b":"Drip"}, ...]`、`pairwise_method=welch_t`、`correction=holm`；重复或反向重复组对会被拒绝。
- `style` 可指定 `font/palette/width/height/summary/show_significance`；尺寸 3–20 英寸，summary 为 mean_sd 或 median_iqr。默认 7×5、DejaVu Sans；颜色必须不透明、不同且足够覆盖全部组。默认配色支持最多 7 组，更多组必须明确扩充调色板。字体不可用或缺所需字符会拒绝，不偷偷换字体。

样本 ID、单位及设计必须由知道数据来源的人确认；`design_confirmed=true` 是记录，不是软件鉴定。请勿机械复制合成示例的 assumptions。

## 输出与追溯

每次分析建立新的目录，包含：

- `analysis.json`：方法、声明假设、统计量、可用效应量/CI、组 n、P/校正 P、缺失行、警告、源和配置哈希、依赖版本、输出哈希。
- `normalized.csv`：进入分析的角色列、数值与原始行号；浮点计算表示，不代替原始数据或精确 Decimal 审计。
- `config.json`：审阅配置快照，源路径缩为文件名，避免泄露本机绝对路径；不是自包含复现实验包，复现需保存原始输入与原始配置及其哈希。
- `figure.svg` / `figure.pdf` / `figure.png`：矢量图和 180 dpi 预览。SVG 保留文字，接收电脑需有对应字体；PDF 字体嵌入由 Matplotlib 处理。

源文件永不改写；读取前后和输出前核对输入哈希。先在临时目录完成全部计算/渲染，通过后发布到不存在的新目录。发布期间发生 I/O 故障会尽量写入 `INCOMPLETE` 标记；强制终止/磁盘故障仍需检查文件完整性。报告不包含自身哈希，最终审阅证据用 `hash/verify` 另存。

原始点在散点图中全部保留，误差线在点上层；随机散开位置 seed=0，不影响数值。括线只用于实际计算的明确组对，星号大小 10 pt；两组检验没有额外的多重校正。显示 ns 不等于证明两组等价。自动范围包含数据和误差线；可见文字做画布边界检查，**文字互相重叠、图例遮点、科学解释仍需实际看图**。

`status=pass` 仅表示本次受支持计算和导出完成。报告明确 `native_prism=false`、`visual_review_required=true`；不保证假设成立或图已达到投稿标准。`summary` 可汇总 analyze 报告，依然不代表全流程验收。

## 与原工作流衔接

1. 新任务先 `inspect`，确认设计/单位/ID/比较家族，选择支持的方法；不支持时停止该分析步骤并记录需求。
2. `analyze` 后核对原始数据、统计结果和每张预览。若复现既有 Prism 分析，另比对其参数与结果，不能用此模块默认方法替换老师的方法。
3. 原生 Prism 继续走 [WORKFLOW.md](WORKFLOW.zh-CN.md)；代码图可把 PDF/SVG 放进 Illustrator，保留来源、方法和字体信息。**没有自动写入 .prism/.ai 的新功能。**
4. 排版由实际轴线/图片边缘定位，填写 `layout` 测量与适用网格规则。项目专属行数、字母、样本量和图例间距不能套用到其他研究。
5. 格式清单使用 `lint --profile generic` 或自定义配置；原项目用 `--profile uwm`。最后核对预览并记录 `verify` 证据。

未实现：生存/Cox、多因素/混合效应、重复测量超过两条件、嵌套样本、复杂调查权重、组学多重检验、空间数据、自动图像分割、任意文件格式和自动判断最佳图型。扩展这些需独立设计、数值基准和视觉测试，不得冒称“任何数据都零错误”。

## 测试案例

| 合成领域 | 要点 |
|---|---|
| 制造公差 | 不等 n、不等方差、Welch 统计量/df 手算复核 |
| 传感器校准 | 负值、打乱顺序、按 ID 配对，不按行配对 |
| 农业产量 | XLSX、ANOVA、指定两组对、Holm 家族 |
| 网站转化 | 2×2 实际计数、枚举超几何分布核对 Fisher P |
| 非线性材料响应 | U 形但 Pearson r 很小；故意展示不适合此形状的模型，不能据 P 否认关系 |
| 服务排名 | 小样本 Spearman 置换；穷举 4! 验证双侧概率 |
| 日能源需求 | TSV、日期、自动时间排序；明确不做时间序列推断 |
| 物流耗时 | 偏态数据、Kruskal 总体检验、median/IQR |

另测：缺失日志、常数退化、重复 ID、公式缓存、百分比声明、非法数值、过期输入、输出防覆盖、缺字体、文字裁切、调色板与通用样式。

方法实现依据官方文档：[Welch t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html)、[配对 t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html)、[ANOVA](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html)、[Kruskal](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html)、[Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)、[Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html)、[Fisher](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)、[Matplotlib 导出](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)、[openpyxl](https://openpyxl.readthedocs.io/en/stable/tutorial.html)。

## 真实生物完整案例

[EXAMPLE_BIOLOGY.zh-CN.md](EXAMPLE_BIOLOGY.zh-CN.md)提供单独的固定 UCI 小鼠蛋白再分析：审计技术重复后汇总、154 项 BH/BY 家族及完整蛋白 PCA。专用 XLS 读取器使用 [science] 中的 xlrd；不代表通用 analyze 已支持任意组学或复现原分层模型。
