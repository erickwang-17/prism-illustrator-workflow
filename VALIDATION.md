# 验证记录

## v0.4 · 可选 API 辅助

2026-11-16 本机 Python 3.13：95 项测试通过（含 21 项新增 API 测试）。配置创建、请求预览及不发送的 ai-ask 已实际运行；完整科学分析回归仍通过。

API 测试使用合成密钥与模拟传输，覆盖两种协议、请求头/超时/响应体限制、401/429/网络失败、无重试、重定向拒绝、配置与请求不一致、密钥替换、拒绝/工具调用/截断输出，以及原分析失败状态保留。测试和 CI 均不调用真实收费服务。

尚未使用用户 API 密钥进行真实服务验收；ai-doctor 只检查本机配置。用户需按 [AI_API.md](AI_API.md) 设置密钥并用合成问题运行一次 --send，另行验证端点、模型权限和额度。AI 建议不等于问题已解决。

## v0.3 · 科学计算与图形

本机验证日期：2026-11-16。以下只描述已执行的检查，不代表所有数据或科学假设必然正确。

- Python 3.13：`python -m unittest discover -v`，74 项测试通过。
- 8 个合成领域的完整流程均生成 SVG、PDF、PNG、结果 JSON 和带来源行号的规范化表；核对原始输入哈希不变。
- 独立手算 Welch t/df、枚举超几何 Fisher 概率、穷举小样本 Spearman 置换、已知 Holm 校正结果通过。
- 示例网站 2×2 表 [[6,2],[1,4]]：双侧 Fisher P=0.10256410256410256，样本 odds ratio=12。
- 乱序配对按 ID 匹配；相同值保留；未确认设计、重复 ID、缺失配对、公式单元格、非有限数、非整数计数和输入在计算中改变等情况被拒绝。
- 图形预览已逐张检查：原始点、误差线、轴范围、标题、n、组对括线和日期标签。长文字越界、缺字、缺字体、透明/重复颜色另有失败测试。
- 安装后的 `figureflow 0.3.0` 已实际运行 inspect 与 analyze；SKILL.md 验证通过。
- 此次科学计算环境：NumPy 2.5.5、SciPy 1.18.1、Matplotlib 3.11.2、openpyxl 3.1.5。每次真实运行会记录自己的依赖版本。

预览：[8 个合成案例](demo-gallery.png)。可用 `python demo_science.py --directory local/demo` 重建；需要预先安装 `.[science]`。不同依赖版本/平台可能有细小数值或字体排版差异，因此不把 PNG 字节相同当作科学正确性的标准。

远程 CI 另在 [GitHub Actions](https://github.com/erickwang-17/prism-illustrator-workflow/actions/workflows/ci.yml) 检查 Python 3.10 和 3.13、全部测试、8 个演示及安装后命令；以对应提交的实际运行结果为准，不以本机通过替代。

尚未验证专有 Prism/Illustrator 宿主自动化，也没有为未支持的生存、混合效应或其他高级模型提供推断。边界与方法完整说明见 [SCIENCE.md](SCIENCE.md)。
