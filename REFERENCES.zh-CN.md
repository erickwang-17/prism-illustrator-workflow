# 设计参考与取舍

[English](REFERENCES.md) | **简体中文**

核查日期：2026-11-16。以下是设计参考，不是依赖清单、官方合作或效果背书。GitHub Stars、论文引用量、下游使用量是不同指标。本次没有获取可复现的论文引用计数，不宣称所有项目在同一指标上排名最高。

官网页面快照显示 uv 约 92.0k Stars、Snakemake 约 2.9k、nf-core/tools 约 331。科研基础设施也按方法适配性选择，不用 Stars 替代科学有效性；其余项目不填未经核对的数值。

| 项目 / 原始资料 | 借鉴做法 | 本仓库落地与边界 |
|---|---|---|
| [uv](https://github.com/astral-sh/uv)、[项目结构](https://docs.astral.sh/uv/concepts/projects/layout/) | 一致的命令入口和项目元数据 | pyproject.toml、可安装 figureflow、--version；保留 Python 直接入口，无 uv 运行时依赖 |
| [Ruff 规则目录](https://docs.astral.sh/ruff/rules/) | 规则编号、诊断与选择范围 | rules / lint、JSON 路径、修正说明；没有冒充 Ruff 规则或自动修复 |
| [Snakemake 配置](https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html) | 配置与处理分离、执行前校验 | schema_version=1 清单、未知字段/类型/必填项检查；不是通用 JSON Schema 引擎 |
| [nf-core/tools](https://nf-co.re/docs/nf-core-tools) | 模板、lint、参数规范与验收文档 | 任务模板、81 项验收、独立格式规则、CI；不将 nf-core 分析模型强加给 Prism |
| [Anthropic Skills](https://github.com/anthropics/skills) | SKILL.md 元数据、按需使用资源 | 根目录 skill 入口，按任务读 README / RULES / WORKFLOW；没有复制整套外部 skill 或安装插件 |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | 需求、计划、任务与结果可追溯 | TASK_TEMPLATE 记录最新/被替代要求、面板范围、证据；不要求小改动写大型规格 |
| [Superpowers](https://github.com/obra/superpowers) | 分步骤工作、测试、完成前验证 | agent 状态恢复和完成证据、历史故障回归；不导入全部代理行为 |
| [pre-commit](https://pre-commit.com/) | 提交前可重复检查 | 可选本地 hook，与 CI 共用 unittest discover；不修改全局 Git hooks |
| [pytest 参数化](https://docs.pytest.org/en/stable/how-to/parametrize.html) | 同一行为覆盖多种边界输入 | 表驱动样本量、数值、正则回归；仍用标准库 unittest，无 pytest 依赖 |
| [MultiQC](https://docs.seqera.io/multiqc) | 汇总已有工具结果，不重新分析 | summary 汇总检查状态与报告哈希；不计算 P 值，不将汇总当完整验收 |
| [Nextflow 恢复](https://docs.seqera.io/nextflow/cache-and-resume) | 根据输入与状态决定能否复用 | 任务记录核对输入/参数/输出/规则版本；尚无 native app 自动缓存执行器 |
| [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) | 模板减少新项目遗漏 | 可复制任务记录、明确标记的模拟清单；不运行外部模板钩子 |

## 采用原则

每个机制必须说明用途和适用范围，能自动验证的部分提供测试。原生软件操作、科学判断和最终图片检查仍独立进行。图形清单必须与真实项目和预览对照。新增规则需具体失败案例，不把本次偏好当成适用于所有实验的定律。

本次实现独立编写，没有复制上游代码或完整文档，没有借用上游商标、许可证或背书。以后引入第三方源码应单独核查许可证并保留必要声明。

不为收集功能同时安装全部框架：基础审计和 API 运行时使用标准库，安装时用 setuptools；科学计算通过可选 [science] 依赖提供。自动原生对象识别、自动提取 Prism 样式、自动选择统计模型和 GUI 恢复均未由这次优化实现。
