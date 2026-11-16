# 图形清单检查协议 v1

`figureflow lint manifest.json` 检查从真实图形提取并核对的声明，不读取 Prism/AI 二进制、不识别图片、不计算 n、不改变原图。更新原生项目后，重新核对清单并与预览一起保存。

`example_manifest.json` 的颜色、样本量、线宽均为模拟输入，不是正式参考值。未测量值不能用示例填充，null 不自动变成默认值。

## 命令

```sh
figureflow rules
figureflow lint example_manifest.json --format text
figureflow lint example_manifest.json --out local/style-report.json
figureflow lint example_manifest.json --select NAM001,LEG001 --error-format json
figureflow summary local/data-report.json local/style-report.json --out local/summary.json
```

先建立 local 目录。--out 只创建新文件。--select 使用完整且无重复的编号；报告包含 selected_rules、full_rule_set 和每条规则实际执行次数。0 次表示未适用，不是已检查。部分通过不等于全图通过。

## 规则

| 编号 | 检查 | 纠正方式 |
|---|---|---|
| NAM001 | group=Vav-Cre 的显示名称必须是 Vav-Cre | 修改原生图例，不改原始观察身份 |
| LEG001 | 末尾恰有一个 `(n=N)`，匹配 audited_n | 先审计独立样本；CMML、AML 各自核对 |
| LEG002 | n_italic 为 true | 将原生样本量后缀设斜体 |
| LEG003 | 图例顺序遵循 reference.group_order | 对所有相关图调整图例，不误移数据 |
| FMT001 | 图与图例字体 Arial | 修正字体并检查重新排版 |
| FMT002 | 散点为原生圆、黑色边框、参考宽度 | 用 Symbols Border 设置，禁止叠加偏移圆 |
| FMT003 | 误差线黑色、在数据点上层、参考宽度 | 核对每组原生设置 |
| FMT004 | 轴文字加粗、无 XTitle、散点无横轴小刻度 | 按图类型设置；其他类型可保留刻度 |
| STA001 | 星号 1–4 个或 ns，Arial 加粗 10 pt | 另保留统计结果，本规则不核对 P 值 |
| COL001 | 每个 group 填充 RGB 精确等于参考值 | 提取数值，不能用相近色 |

## 字段合同

顶层仅允许 schema_version（整数 1）、reference、非空 panels。未知字段、重复 JSON 键、错误类型、缺失字段报输入错误。

- reference：group_order、相同 group 键的 palette（#RRGGBB）、正数 border_width_pt / error_width_pt。
- panel：id、kind（scatter/line/survival/bar）、font、axis_bold、x_ticks、x_title、legends、stars、error_bars。图片走布局与视觉检查。
- legend：group、label、正整数 audited_n、n_italic、font、symbol、native、border_color、正数 border_width_pt、fill。布尔值不能写成字符串。
- star：text、font、bold、size_pt。没有标注时 stars=[]，不代表已验证标注无遗漏。
- error_bars：color、layer、width_pt。非散点且无误差线可为 null；当前散点协议要求提供测量设置。

group 是机器 ID，显示文字可以使用 Unicode。NA_KO_CMML / NA_KO_AML 可用于同一横轴组的不同图例。本协议不检查其真实横轴位置是否合并。所有样式声明均需与原生对象核对。

## 正则与边界

| 目的 | Python 正则 | 边界 |
|---|---|---|
| n 后缀 | `\(n=([1-9][0-9]*)\)\Z` | ASCII 正整数；拒绝 n=0、缺失、尾部换行；再比较 audited_n |
| RGB | `#[0-9A-Fa-f]{6}\Z` | 精确 RGB；大小写等价 |
| ID | `[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z` | 长度上限 64；不含路径分隔符 |
| 星号 | `(?:\*{1,4}|ns)\Z` | 拒绝 5 个星号和尾部文字 |

只运行固定、有限制模式，不接受用户提供的正则或全局改写科研文本。群组语义、斜体、边框、图层不能通过正则推断。

## 报告和退出码

报告含 report_version=1、tool_version、command 和输入哈希。lint 诊断含 code、severity、JSON path、message、fixable=false。0=当前范围通过，1=发现问题，2=输入/文件错误。

--error-format json 将运行期输入/文件错误放在 stderr，stdout 保持为空；命令行用法错误仍为 argparse 文本。消费者应允许新增字段、拒绝未知 report_version。

summary 只接受版本 1 的 audit/plan/layout/verify/lint 报告，保留状态、版本、范围及报告哈希。任一 fail 则汇总 fail；不重跑、不验证输入仍新鲜、不证明范围完整。最终仍需 verify 与视觉验收。
