<!-- About 简介（推送后填写到仓库 About 栏）：
期刊论文助手：选题→IMRaD框架→分节写作→图表规范→投稿前自查→返修信 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-paper
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, paper, academic-writing, journal -->

# lhg-paper：期刊论文助手，选题到返修的全流程

> ## 学术诚信声明
>
> 本插件是**写作助手**，不是代写工具。它帮你提炼创新点、搭 IMRaD 框架、
> 顺写作逻辑、查图表格式、模拟审稿、写返修信，但**论文的观点、数据、
> 实验结果、结论必须是你的原创研究**。
>
> 1. **AI 辅助写作披露**：多数期刊要求声明 AI 工具的使用范围（通常允许语言润色）。
>    投稿前务必阅读目标期刊作者指南中关于 AI 的条款，如实披露。
> 2. **遵守目标期刊政策**：一稿多投、重复发表、图片不当处理等行为各期刊均明令禁止。
> 3. **原创性责任在作者**：引用必须真实读过，不编造文献、不编造数据。
>
> 涉及学术不端的请求（如"帮我编几篇参考文献""数据不好看帮我改改"），本插件一律拒绝。

> **一句话介绍**：给 AI 编程助手装上"期刊论文流水线"——选题→创新点提炼→IMRaD 框架→分节写作→图表规范→投稿前自查→审稿意见返修应对，10 条确定性审计规则，学术诚信先行。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-paper
> /plugin install lhg-paper@lhg-plugs
> ```

## 它是什么

`lhg-paper` 是一个 Claude Code 插件（plugin 为主、skill 为辅），区别于 `lhg-thesis`
（学位论文版）：本插件侧重**期刊发表流程**——创新点强度与期刊档位匹配、
图表门面工程、投稿前自查、审稿意见返修信。

- **3 个命令**（小白入口）：`paper` 全流程（选题→框架→写作→图表→自查→返修信），
  `paper-audit` 投稿前自查，`paper-figure` 图表规范专项
- **3 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：
  选题与框架、学术写作规范、投稿前自查+返修应对
- **3 个专家 agent**：选题框架专家、审稿人模拟专家、图表规范专家
- **2 个 hooks**：导出/提交前审计拦截（硬门，可一键豁免）、写章节时图片缺图题提醒（警告级）
- **10 条确定性审计规则**：纯 Python、零第三方依赖

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-paper:paper` | 选题→IMRaD框架→分节写作→图表规范→投稿前自查→返修信，全流程 | `/lhg-paper:paper "小样本图像分类" "计算机学报"` |
| `/lhg-paper:paper-audit` | 投稿前自查：引用/图表/摘要/关键词/口语化/伦理声明 | `/lhg-paper:paper-audit ./my-paper` |
| `/lhg-paper:paper-figure` | 图表规范：编号连续、图题自明、三线表、分辨率 | `/lhg-paper:paper-figure ./my-paper` |

## 目录结构

```
lhg-paper/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：paper / paper-audit / paper-figure
├── skills/                  # 3 个平台中立 skill（选题框架/写作规范/自查返修）
├── agents/                  # 3 个专家 agent（outliner / reviewer / figure）
├── hooks/                   # 投稿前审计拦截 + 图片缺图题提醒（均可一键关闭）
├── scripts/audit/           # 确定性审计：paper_audit.py（零第三方依赖）
├── fixtures/                # 好/坏论文对照用例
├── smoke_test.py            # 冒烟测试
├── ATTRIBUTION.md           # 灵感来源声明
└── LICENSE                  # MIT
```

## 论文目录约定

```
my-paper/
├── paper.yaml           # 题目/作者/目标期刊（可选，有它 hook 识别更准）
├── sections/
│   ├── 01-abstract.md
│   ├── 02-introduction.md
│   ├── 03-methods.md
│   ├── 04-results.md
│   ├── 05-discussion.md
│   └── 06-conclusion.md
├── references.bib       # BibTeX 参考文献
└── figures/             # 图片源文件
```

## 什么时候用 / 什么时候不用（FAQ）

**Q：和 lhg-thesis（毕业论文助手）有什么区别？**
A：`lhg-thesis` 走"开题→盲审"的学位论文路线，重 GB/T 7714 与学校格式；
`lhg-paper` 走"选题→投稿→返修"的期刊路线，重创新点强度匹配、图表门面、
返修信。写期刊论文用本插件，写学位论文用 thesis。

**Q：能保证论文被接收吗？**
A：**不能，也不承诺**。本插件提高的是"不因格式/逻辑硬伤被秒拒"的概率，
创新性与工作量本身才是接收的决定因素，任何"包接收"的说法都是不诚实的。

**Q：这是代写工具吗？**
A：不是。本插件是写作助手：框架、逻辑、格式、评审模拟可以帮你，但观点、
数据、结论必须是你的原创研究。编造文献/数据的请求会被直接拒绝。

**Q：用 AI 帮我写论文，期刊会查吗？**
A：多数期刊要求披露 AI 使用情况（通常允许语言润色）。本插件在主流程第一步
就会提醒你读目标期刊的 AI 政策并如实披露。隐瞒 AI 使用一旦被发现，
后果比语言问题严重得多。

**Q：一定要用 Claude Code 吗？**
A：`skills/` 下的方法论是平台中立的纯 Markdown，可直接搬到豆包、Workbuddy
等 agent 平台用。只有 commands/agents/hooks 需要 Claude Code。

## 自迭代

- 每个 skill 末尾有「自检与反馈」节：质检门 + 标准冒烟用例 + 一键提 issue。
- 发现规则误报/漏报、方法论不合理：到本仓库提 issue（标题带对应 skill 前缀，
  如 `[lhg-paper-audit]`），附学科领域与场景描述。

## 更多插件

lhg-plugs「小白专家插件」组织级索引（含全部插件矩阵）：
https://github.com/lhg-plugs/marketplace

## 出品：刘洪光

刘洪光（https://github.com/lhg-skills）出品，lhg-plugs「小白专家插件」系列之一。
灵感来源见 [ATTRIBUTION.md](./ATTRIBUTION.md)（借鉴思路，实现与文案均为原创）。
