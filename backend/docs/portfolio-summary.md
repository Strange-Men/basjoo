# 作品集摘要｜Portfolio Summary

> **面向**：中国 HR / 技术面试官 / 作品集访问者

---

## 项目定位

基于开源 AI 客服平台 [Basjoo](https://github.com/haoyiyin/basjoo) 进行二次开发，重点补充 **RAG 质量评估能力**和**可复现的工程验证体系**。

**不是从 0 写客服机器人**，而是在一个真实开源项目上做工程质量增强。

### 为什么选 Basjoo？

| 理由 | 说明 |
|---|---|
| MIT License | 最宽松的开源协议，学习和二开完全无限制 |
| 技术栈主流 | Python/FastAPI + Next.js 14 + PostgreSQL + Qdrant |
| 项目规模适中 | 7.2MB 代码库，单体架构，二开难度低-中 |
| 测试覆盖出色 | 35+ 后端测试文件 + Playwright E2E 测试 |
| RAG 管道完整 | Qdrant 向量搜索 + 文档解析 + chunking + embedding |

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.11+ / FastAPI |
| 前端 | TypeScript / Next.js 14 |
| 数据层 | PostgreSQL + Qdrant（向量搜索） |
| 部署 | Docker Compose |
| 测试 | pytest / Playwright |
| 评估 | 自研 RAG Evaluation Harness |

---

## 我负责的内容

### Phase 1：RAG Evaluation Harness（v1.0）

**问题**：Basjoo 有完整的 RAG 管道，但没有任何系统化的 RAG 质量评估机制。

**方案**：构建了一套 mock 友好的评估框架：
- Mock Embedding：基于字符频率的 256 维向量，无需 API Key
- Mock Retriever：基于内存的余弦相似度搜索，无需 Qdrant
- Mock Pipeline：从检索结果中提取答案，无需调用 LLM

**结果**：37 个 pytest 测试全部通过，15 个 eval cases 全部通过。

### Phase 2：SmartHome Demo Data（v1.1）

**问题**：没有现成的测试数据用于智能家居客服场景。

**方案**：创建了完整的演示数据集：
- 2 个 Demo Agent + 3 篇知识库文档
- 15 个 Demo 问题 + 3 个对话场景 + 8 个 Bad Cases

**结果**：`seed_demo_data.py` 支持 3 种模式（validate-only、dry-run、mock）。

### Phase 3：文档与报告（v1.2）

**问题**：文档不完整，报告不够正式。

**方案**：完善所有文档：
- 增强评估报告，增加执行摘要
- 创建作品集摘要（本文件）
- 添加增强概述
- 改进使用文档

**结果**：专业级文档，适合作品集展示。

---

## 工程亮点

### 1. Mock RAG Pipeline

**挑战**：如何在没有真实 API 的情况下测试 RAG 质量？

**方案**：设计了确定性的 mock pipeline：
- **Mock Embedding**：字符频率向量（256 维）— 相同输入永远产生相同向量
- **Mock Retriever**：内存余弦相似度 — 无外部依赖
- **Mock Pipeline**：提取式答案 — 从 chunks 中复制相关句子

**体现的能力**：理解 embedding 空间、相似度搜索、RAG 架构。

### 2. 评估指标体系

**挑战**：如何衡量 RAG 质量？

**方案**：实现了标准 IR 指标：
- **Precision@k**：top-k 结果中相关文档的比例
- **Recall@k**：相关文档中被检索到的比例
- **MRR**：第一个相关结果的排名倒数的平均值
- **No-Answer Accuracy**：无关查询的正确拒答率
- **Citation Accuracy**：引用来源的正确率
- **Hallucination Risk**：编造事实的数量

**体现的能力**：信息检索评估方法论。

### 3. 可复现测试

**挑战**：如何确保测试是确定性的、CI 友好的？

**方案**：
- 不需要 API Key
- 不需要外部服务（无 Docker、无 Qdrant）
- 确定性的 mock 组件
- JSON fixtures 管理测试数据

**体现的能力**：工程纪律和 CI/CD 意识。

### 4. Demo Data 设计

**挑战**：如何创建逼真的测试数据？

**方案**：
- 模拟真实客服场景
- 包含边界情况（无答案、低相关性）
- 添加对抗性用例（幻觉陷阱）
- 结构化设计，同时服务于测试和作品集展示

**体现的能力**：测试设计和数据建模。

---

## 测试结果

### RAG Eval 测试

```
tests/rag_eval/: 37 passed
```

### 评估 Runner

```
总用例数：15
通过：15（100%）
失败：0（0%）

Precision@3: 0.567
Recall@3: 0.978
Precision@5: 0.527
Recall@5: 1.000
MRR: 0.600

No-Answer Accuracy: 100.0%
Citation Accuracy: 88.9%
Hallucination Risk Cases: 0
```

### 基线安全检查

```
原有测试：267 passed, 36 failed, 1 skipped（无变化）
新增回归：0
```

---

## 面试讲解话术

### "介绍一下这个项目"

"我在开源 AI 客服平台 Basjoo 上做了二次开发，重点是 RAG 质量评估。我构建了一套评估框架，可以测试检索精度、无答案处理、引用准确性和幻觉风险。关键挑战是如何在没有真实 API Key 的情况下做测试 — 我设计了一套 mock pipeline，使用字符频率向量和内存相似度搜索，让测试变得确定性和 CI 友好。"

### "最难的部分是什么？"

"设计 mock embedding 系统。我需要一个不需要调用真实 embedding API 就能产生一致相似度分数的东西。最终选择了字符频率向量 — 它们不是语义的，但是确定性的、快速的。权衡是指标不反映真实 RAG 质量，但能验证评估框架本身是否正确。"

### "你会怎么做不同？"

"生产环境我会接入真实 embedding（Jina 或 OpenAI）和真实向量库（Qdrant）。Mock pipeline 适合开发和测试，但真实 RAG 质量依赖语义理解。我还会加上延迟指标和多轮对话评估。"

### "你学到了什么？"

"三件事：第一，可复现测试的重要性 — mock 组件让我快速迭代，不用付 API 调用费用。第二，RAG 评估的复杂性 — precision/recall 只是基础，还需要检查幻觉和引用准确性。第三，文档的重要性 — 文档完善的项目更容易维护和展示。"

---

## 简历 Bullet

### 中文版（适合直接放简历）

> 基于开源 AI 客服系统 Basjoo 进行二次开发，构建 RAG Evaluation Harness 与 SmartHome Demo Data，覆盖检索命中、无答案回退、证据引用、幻觉风险等 15 类评估用例，并通过 pytest 与独立 runner 生成 JSON / Markdown 评估报告。设计 Mock Embedding / Retriever / Pipeline 实现无 API Key、无 Qdrant 环境下的可复现评估。

### English Version

> Enhanced an open-source AI customer support platform (Basjoo) by adding a mock-friendly RAG evaluation harness with 15 eval cases covering retrieval precision, no-answer fallback, citation accuracy, and hallucination risk. Built deterministic mock pipeline enabling reproducible evaluation without API keys or external services.

### 详细版（适合作品集）

- 设计并实现 RAG 评估框架，包含 15 个测试用例，覆盖 6 类场景
- 构建基于字符频率向量的 Mock Embedding 系统，实现确定性、无 API Key 的测试
- 实现标准 IR 指标：Precision@k、Recall@k、MRR、No-Answer Accuracy、Citation Accuracy
- 创建 SmartHome 演示数据集：2 个 Agent、3 篇知识文档、15 个问题、3 个对话、8 个 Bad Cases
- 达成 37 个 pytest 测试全部通过，15/15 eval cases 全部通过，无回归
- 生成 JSON + Markdown 评估报告，含执行摘要和指标分析

---

## 不夸大的边界说明

### 当前成果的真实价值

- ✅ 提供了一套可复现的 RAG 评估框架
- ✅ 提供了一套完整的 SmartHome Demo 数据
- ✅ 验证了评估逻辑的正确性（测试通过、指标计算正确）
- ✅ 没有对原有项目产生回归
- ✅ 所有工作可以在无 API Key 环境下复现

### 当前成果的局限

- ❌ Mock 指标不代表真实线上 RAG 效果
- ❌ 字符频率向量不是语义向量
- ❌ 提取式回答不是 LLM 生成的回答
- ❌ 评估用例是手动设计的，不是自动生成的
- ❌ 没有多轮对话评估
- ❌ 没有延迟/性能指标

### 真实评估需要什么？

- Jina / OpenAI Embedding API（替换 Mock Embedding）
- Qdrant 向量库（替换 Mock Retriever）
- LLM API（替换 Mock Pipeline）
- 框架已预留扩展接口，只需替换实现即可

---

## 项目链接

| 资源 | 链接 |
|---|---|
| 管理仓库 | https://github.com/Strange-Men/CustomerOpsAgent_2 |
| 代码仓库 | https://github.com/Strange-Men/basjoo/tree/phase1-rag-eval-harness |
| 增强概述（中文） | [ENHANCEMENT_SUMMARY.zh-CN.md](../../ENHANCEMENT_SUMMARY.zh-CN.md) |
| 增强概述（英文） | [ENHANCEMENT_SUMMARY.md](../../ENHANCEMENT_SUMMARY.md) |
| RAG 评估文档 | [rag-evaluation.md](rag-evaluation.md) |
| 评估报告 | [../reports/rag_eval_report.md](../reports/rag_eval_report.md) |

---

*版本：v1.3-phase1-complete*
*最后更新：2026-06-20*
