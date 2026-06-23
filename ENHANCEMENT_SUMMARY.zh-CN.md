# Basjoo 二次开发增强说明（中文版）

> **面向**：技术审查 / 工程记录
> **分支**：`phase1-rag-eval-harness`
> **当前版本**：v2.1.2

---

## 1. 项目背景

[Basjoo](https://github.com/haoyiyin/basjoo) 是一个开源的 AI 客服平台，基于 Python/FastAPI + Next.js 14 + PostgreSQL + Qdrant 构建，MIT License。

**我在 Basjoo 的基础上做了什么？**
- 补充了一套 **RAG Evaluation Harness**（RAG 评估测试框架）
- 创建了 **SmartHome Support Demo Data**（智能家居客服演示数据）
- 生成了 **JSON + Markdown 评估报告**
- 全部工作可以在**无 API Key、无 Qdrant、无 Docker** 的环境下复现

**不是从 0 写客服机器人**，而是在一个真实开源项目上做工程质量增强。

---

## 2. 二开目标

| 目标 | 说明 |
|---|---|
| **填补 RAG 评估空白** | Basjoo 有完整的 RAG 管道，但没有任何质量评估机制 |
| **不破坏原项目** | 所有代码都是纯新增，不修改任何核心文件 |
| **可复现** | 不需要 API Key、不需要 Qdrant、不需要 Docker 就能跑测试 |
| **适合作品集** | 有量化指标、有评估报告、有 demo 数据 |

---

## 3. 我新增了什么

### 3.1 RAG Evaluation Harness（v1.0）

一套轻量级、mock 友好的 RAG 评估测试框架。

| 组件 | 说明 |
|---|---|
| **15 个 eval cases** | 覆盖 6 类场景：正常命中、多文档检索、无答案回退、低相关度拒答、evidence/citation 校验、幻觉风险 |
| **Mock Embedding** | 基于字符频率的 256 维向量，无需 API Key |
| **Mock Retriever** | 70% 关键词重叠 + 30% 向量余弦相似度的混合评分 |
| **Mock RAG Pipeline** | 从检索结果中提取答案，无需调用 LLM |
| **37 个 pytest 测试** | 全部通过 |
| **评估指标** | Precision@k、Recall@k、MRR、No-Answer Accuracy、Citation Accuracy、Hallucination Risk |
| **JSON + Markdown 报告** | 自动生成评估报告 |

### 3.2 SmartHome Demo Data（v1.1）

一套可复用的智能家居客服演示数据集。

| 组件 | 说明 |
|---|---|
| **2 个 Demo Agent** | 通用客服 + 退换货专员，含 system prompt 和升级策略 |
| **3 篇知识库文档** | 产品 FAQ（2.3KB）、退换货政策（2.3KB）、故障排除指南（3.3KB） |
| **15 个 Demo 问题** | 11 个可回答 + 4 个不可回答，覆盖保修、退货、物流、故障、无关问题 |
| **3 个对话场景** | 正常咨询、升级处理、无答案回复 |
| **8 个 Bad Cases** | 幻觉陷阱、政策编造、跨文档混淆、混合语言 |
| **seed_demo_data.py** | 支持 `--validate-only`、`--dry-run`、`--mock` 三种模式 |

### 3.3 文档与报告（v1.2）

| 组件 | 说明 |
|---|---|
| **ENHANCEMENT_SUMMARY.md** | 增强概述、文件地图、运行说明、测试结果 |
| **rag-evaluation.md** | 正式使用文档，含架构图、指标说明、扩展指南 |
| **portfolio-summary.md** | 作品集/面试指南，含技术亮点、面试话术、简历 bullet |
| **rag_eval_report.md** | 正式评估报告，含执行摘要、指标表格、场景覆盖 |
| **reports/README.md** | 报告文档，说明如何生成和解读 |

### 3.4 真实 Qdrant 检索评估（v2.0）

将 mock 评估框架扩展为支持真实 Qdrant + SiliconFlow 检索评估。

| 组件 | 说明 |
|---|---|
| **seed_demo_data.py --write-db** | 将 demo 知识库写入 Qdrant，使用真实 embedding |
| **run_rag_eval.py --real** | 对 5 个 eval cases 运行真实检索评估 |
| **SiliconFlow Qwen3-Embedding-0.6B** | 1024 维 embedding 模型 |
| **Qdrant REST API** | 向量检索（urllib，避免 qdrant_client 版本问题） |
| **rag_eval_real_report.json/md** | 真实评估报告 |
| **rag_eval_mock_vs_real.md** | Mock vs Real 对比报告 |
| **test_real_eval_config.py** | 7 个配置测试（不依赖真实 API） |

---

## 4. 文件地图

```
backend/
├── tests/
│   └── rag_eval/
│       ├── conftest.py                    # Mock embedding/retriever/pipeline
│       ├── fixtures/
│       │   ├── demo_knowledge_base.json   # v1.0 知识库 fixture
│       │   ├── demo_knowledge_base_full.json  # v1.1 扩展知识库
│       │   └── rag_eval_cases.json        # 15 个评估用例
│       ├── test_retrieval_precision.py    # 检索精度测试
│       ├── test_no_answer_fallback.py     # 无答案回退测试
│       ├── test_evidence_citation.py      # 引用准确性测试
│       ├── test_hallucination_risk.py     # 幻觉检测测试
│       └── test_demo_data_integrity.py    # Demo 数据完整性测试
├── scripts/
│   ├── run_rag_eval.py                    # 独立评估 runner
│   ├── seed_demo_data.py                  # Demo 数据种子脚本
│   └── demo_data/
│       ├── agents.json                    # 2 个 Demo Agent 配置
│       ├── demo_questions.json            # 15 个 Demo 问题
│       ├── conversations.json             # 3 个对话场景
│       ├── expected_evidence.json         # 引用来源映射
│       ├── bad_cases.json                 # 8 个对抗性测试用例
│       └── knowledge/
│           ├── product_faq.md             # 产品 FAQ
│           ├── return_policy.md           # 退换货政策
│           └── troubleshooting.md         # 故障排除指南
├── reports/
│   ├── rag_eval_report.json              # 机器可读报告
│   ├── rag_eval_report.md                # 人类可读报告
│   └── README.md                         # 报告文档
└── docs/
    ├── rag-evaluation.md                  # 使用文档
    └── portfolio-summary.md              # 作品集指南

ENHANCEMENT_SUMMARY.md                     # 英文增强概述
ENHANCEMENT_SUMMARY.zh-CN.md              # 本文件（中文版）
```

---

## 5. 如何运行

### 运行 pytest 测试

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests\rag_eval -v
```

### 运行评估 runner（mock 模式）

```powershell
cd backend
.\venv\Scripts\python.exe scripts\run_rag_eval.py --mock
```

输出文件：
- `reports/rag_eval_report.json` — 机器可读
- `reports/rag_eval_report.md` — 人类可读

### 运行 Demo Data Seeder

```powershell
cd backend

# 验证 JSON 格式（无副作用）
.\venv\Scripts\python.exe scripts\seed_demo_data.py --validate-only

# 预览数据摘要
.\venv\Scripts\python.exe scripts\seed_demo_data.py --dry-run

# 生成 mock 知识库 fixture
.\venv\Scripts\python.exe scripts\seed_demo_data.py --mock
```

### 三种模式对比

| 模式 | 读取 | 写入 | 用途 |
|---|---|---|---|
| `--validate-only` | demo_data/*.json | 无 | CI 验证、提交前检查 |
| `--dry-run` | demo_data/*.json | 无 | 预览数据摘要 |
| `--mock` | demo_data/*.json, knowledge/*.md | `fixtures/demo_knowledge_base_full.json` | 生成扩展知识库 fixture |

---

## 6. 测试结果

### RAG Eval 测试

```
tests/rag_eval/: 37 passed
```

### 评估 Runner（Mock 模式）

```
总用例数：15
通过：15（100%）
失败：0（0%）

检索指标：
- Precision@3: 0.567
- Recall@3: 0.978
- Precision@5: 0.527
- Recall@5: 1.000
- MRR: 0.600

质量指标：
- No-Answer Accuracy: 100.0%
- Citation Accuracy: 88.9%
- Hallucination Risk Cases: 0
```

### Demo Data Seeder

```
--validate-only: PASS
--dry-run: PASS
--mock: PASS
```

### 基线回归测试

| 指标 | 改动前 | 改动后 | 变化 |
|---|---|---|---|
| 原有测试 | 267 passed, 36 failed, 1 skipped | 267 passed, 36 failed, 1 skipped | 无变化 |
| 新增 RAG eval 测试 | — | 37 passed | +37 |
| 新增回归 | — | 0 | 无 |

---

## 7. Mock / No-API-Key 策略

### 为什么用 Mock 模式？

1. **验证评估框架本身** — 不是验证真实 RAG 质量
2. **不需要密钥** — 安全，适合 CI/CD 和本地开发
3. **确定性** — 相同输入产生相同输出
4. **轻量级** — 不引入重型依赖（不用 RAGAS、DeepEval、LangChain）

### Mock 实现对比

| 组件 | Mock 实现 | 真实等价物 |
|---|---|---|
| Embedding | 字符频率向量（256 维） | Jina API / OpenAI Embeddings |
| Retriever | 内存余弦相似度 | Qdrant 向量搜索 |
| Pipeline | 提取式（从 chunks 中复制） | LLM 生成回答 |
| Knowledge Base | JSON fixture | PostgreSQL + Qdrant |

### 这证明了什么？

- 测试结构正确且可运行
- 指标计算逻辑正常工作
- 评估用例覆盖了目标场景
- 报告生成输出有效
- 没有对原有测试产生回归

---

## 8. 当前限制

1. **Mock embedding 是基于字符的，不是语义的** — 余弦相似度是近似的
2. **Mock pipeline 不使用真实 LLM** — 答案是从 chunks 中提取的，不是生成的
3. **评估用例是手动设计的** — 不是自动生成的
4. **没有多轮对话评估** — 只评估单轮
5. **没有延迟/性能指标** — 只关注质量
6. **真实模式只评估检索** — 不评估 LLM 回答生成和幻觉检测
7. **不做 API 级别 chat eval** — 只评估检索质量
8. **不做 LLM 回答生成评估** — 不评估 LLM 回答质量
9. **不做前端展示** — 不包含 UI 组件
10. **不做线上部署** — 只是评估框架

## 9. 安全说明

- `.env` 文件不提交到仓库
- API Key 不写入文档
- 报告不包含真实 key

---

## 10. 版本历史

### v2.1.1 — Real Eval Case Expansion

- Real eval cases 从 5 个扩展到 10 个
- 覆盖全部 6 种 scenario 类型：normal_hit、multi_doc_retrieval、no_answer_fallback、low_relevance_reject、evidence_citation、hallucination_risk
- 包含中英文 cases
- 50 个 pytest 测试全部通过
- Mock eval 继续 15 cases 全部通过
- Real eval 变成 10 cases，全部通过

### v2.1.2 — Mismatch Analysis

- 新增 `_compute_mismatch()` 函数，为每个 real eval case 计算 mismatch 分析
- 新增字段：`language`、`returned_sources_top3`、`matched_sources`、`missing_sources`、`unexpected_sources`、`mismatch_type`、`analysis_note`
- `mismatch_type` 枚举：none、missing_expected_source、unexpected_source_in_top3、low_rank_expected_source、no_answer_with_retrieval_noise、low_confidence_match
- 新增 6 个 pytest 测试（TestMismatchAnalysis），纯逻辑测试，不调用 API
- 50 个 pytest 测试全部通过
- 关键发现：Precision@3=0.600 是 metric artifact（no-answer cases 拉低），实际 normal cases 为 1.000
- 关键发现：TC004 是唯一真实检索问题（return_policy.md 未进 top-5）

---

## 11. 下一步计划

### v2.1.3 — 报告格式和文档收尾（当前）

- 收尾报告格式和文档
- 添加版本历史和变更说明
- 添加指标解释
- 添加限制说明和安全说明

### v2.1.4 — 质量审计和 freeze tag

- 质量审计 v2.1.x 变更
- 创建 v2.1.x freeze tag

### v3.0 — 完整 RAG 管道评估（未来）

- 集成真实 LLM chat endpoint
- 评估真实回答的幻觉问题
- 多轮对话评估

---

*版本：v2.1.2*
*最后更新：2026-06-23*
