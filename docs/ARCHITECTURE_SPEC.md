# Clinical Reasoning Agent — Architecture Specification v0.3

> **来源**：三家 AI 架构师建议 + 项目所有者决策收敛
> **用途**：直接指导编码的最终架构定义
> **日期**：2026-05-11（迁移至 clinical_reasoning_agent 项目）
> **版本**：v0.3 MVP（第三次收敛 — 最终决策落地）
> **迁移自**：`kg_system/design_advice/medical/03_architecture.md`

---

## 目录

1. [最终架构图](#1-最终架构图)
2. [层结构定义（L0-L8）](#2-层结构定义最终版-l0-l78层)
3. [数据库 Schema](#3-数据库-schema)
4. [模块接口定义](#4-模块接口定义)
5. [AgentState 数据流](#5-agentstate-数据流)
6. [路径约束规则](#6-路径约束规则)
7. [诊断逻辑层](#7-诊断逻辑层diagnostic-logic-layer)
8. [中英文语言策略](#8-中英文语言策略)
9. [Config 结构](#9-config-结构)
10. [依赖清单](#10-依赖清单)
11. [文件清单与职责](#11-文件清单与职责)
12. [实现优先级](#12-实现优先级)

---

## 1. 最终架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                         交互层                                     │
│  ┌─────────────────────┐    ┌────────────────────────────────┐   │
│  │  专家模式            │    │  演示模式 (DEMO_MODE=true)      │   │
│  │  结构化JSON输入      │    │  自然语言输入                   │   │
│  └────────┬────────────┘    └──────────────┬─────────────────┘   │
└───────────┼───────────────────────────────┼─────────────────────┘
            ▼                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  实体抽取层                                                       │
│  ┌─────────────────────┐    ┌────────────────────────────────┐   │
│  │  专家模式            │    │  演示模式                       │   │
│  │  JSON.parse → 直接读  │    │  entity_extractor.py           │   │
│  └────────┬────────────┘    │  词典 + 正则 + 否定检测 + 分度    │   │
│           │                 └──────────────┬─────────────────┘   │
└───────────┼───────────────────────────────┼─────────────────────┘
            ▼                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  实体标准化层                                                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  aliases 表映射：中文/同义词 → 英文标准节点名              │    │
│  │  分度映射：40° → SLR_40deg_mild                          │    │
│  │  否定标记：negated=True → 排除路径                       │    │
│  └──────────────────────┬───────────────────────────────────┘    │
└─────────────────────────┼──────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  图谱推理层 (path_retriever.py)                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  SQLite → 读 edges → NetworkX DiGraph 构建                │    │
│  │  关系白名单过滤（按 path_type 选择）                       │    │
│  │  深度限制：max_depth=3                                    │    │
│  │  层级单调性检查：layer 序列不回退超过 1 级                 │    │
│  │  路径类型：mech_path（L0→L4）/ diag_path（L4/L5→L6）      │    │
│  │   inter_path（L6→L7） / 禁忌节点过滤                      │    │
│  └──────────────────────┬───────────────────────────────────┘    │
└─────────────────────────┼──────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  诊断逻辑层 (reasoning/diagnostic_matcher.py) ★ 新增               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  症状+体征 → 模式匹配 → 推断机制（见 §7）                 │    │
│  │  输入：症状(L4) + 检查(L5) 节点                           │    │
│  │  输出：推断的病理机制(L2) 或 损伤路径(L1)                 │    │
│  │  存储：diagnostic_rules 表                                 │    │
│  └──────────────────────┬───────────────────────────────────┘    │
└─────────────────────────┼──────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  RAG 检索层 (retrieval/)                                           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  ① graph_searcher：图谱路径检索                          │    │
│  │  ② 取路径命中节点的 node_id 集合                         │    │
│  │  ③ chunk_searcher：仅在这些节点关联的 chunks 内搜索       │    │
│  │  ④ FAISS 语义重排 → top_k=3                              │    │
│  │  ⑤ 无命中 → fallback: 全库 FAISS 搜索                    │    │
│  └──────────────────────┬───────────────────────────────────┘    │
└─────────────────────────┼──────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  SOAP 生成层 (generation/soap_generator.py)                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  ① 模板填充（代码执行）                                       │    │
│     ├─ S: 患者主诉 [症状列表]，[加重因素] 时加重               │    │
│     ├─ O: [体征列表]；影像提示 [发现]                        │    │
│     ├─ A: [诊断]，机制为 [因果链]，支持证据 [检+诊]           │    │
│     └─ P: ①祛因 ②控制 ③训练 ④治疗（按优先级排列）            │    │
│  ② LLM 润色（DeepSeek, JSON模式, temperature=0.2）            │    │
│     → 校验 JSON schema → 失败重试(max 2)                      │    │
│  ③ 证据绑定：每条结论附带 [source_ref]                        │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  输出层                                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  SOAP 报告（中文显示）                                      │    │
│  │  + 诊断推理路径（A 部分显式展示）                           │    │
│  │  + 干预优先级排序（P 部分按祛因→训练→医疗排列）             │    │
│  │  + 免责声明（强制）                                         │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 数据流（单次推理）

```
用户输入
  → entity_extractor.extract(text)              → entities list
  → repository.resolve_entities(entities)        → standard node names
  → diagnostic_matcher.match(L4+L5 nodes)        → inferred mechanism (L2)
  → path_retriever.find_paths(nodes, path_type)  → graph_paths list
  → graph_searcher.retrieve(path_node_ids, query)→ chunks list
  → soap_generator.fill_template(state)          → draft report
  → soap_generator.llm_polish(draft)             → final SOAP
  → disclaimer.append(output)
```

---

## 2. 层结构定义（最终版 L0-L7，8层）

| 层级 | 名称 | 内容 | 示例节点 | 备注 |
|:----:|:----|:-----|:---------|:----:|
| **L0** | Behavior / Exposure | 动作、行为模式、暴露 | `Lumbar_Flexion`, `Prolonged_Sitting`, `Repeated_Bending` | 诱因层 |
| **L1** | Mechanical Load | 生物力学负荷（按损伤路径细分） | `Flexion_Compression`, `Disc_Shear`, `Repetitive_Low_Load` | ⭐ L1 内部 subtype 细分 |
| **L2** | Tissue Pathology | 组织/病理损伤 | `Disc_Herniation`, `Annulus_Tear`, `Facet_Irritation` | |
| **L3** | Pathophysiology | 病理生理机制（客观） | `Nerve_Root_Compression`, `Inflammation`, `Instability` | 独立层，非症状 |
| **L4** | Symptoms | 主观症状体验 | `Low_Back_Pain`, `Radicular_Pain`, `Numbness` | 与 L3 分开 |
| **L5** | Clinical Evidence | 体征/检查（客观） | `SLR_40deg_mild`, `MRI_Disc_Protrusion`, `Flexion_Test_Positive` | type 分 provocation / imaging / functional |
| **L6** | Diagnostic Logic | 模式识别与推理规则 | `Flexion_Pain+SLR+ → Discogenic_Pain` | ⭐ 新增核心层（§7 详解） |
| **L7** | Intervention | 干预（5 子类） | 见下方拆分表 | ⭐ 内部强制拆分 |
| **L8** | Outcome | 预后结局 | `Pain_Relief`, `Return_To_Work`, `Recurrence` | |

### L7 干预内部分类（强制执行）

| 子类 | 英文标识 | 示例 | 说明 |
|:----:|:--------|:-----|:----:|
| **L7a** | Remove Cause | `Avoid_Flexion`, `Modify_Lifting_Pattern` | ✅ 第一步：消除诱因 |
| **L7b** | Exercise Therapy | `Core_Stabilization`, `Bird_Dog`, `Curl_Up` | 康复训练 |
| **L7c** | Passive Therapy | `Manual_Therapy`, `Traction`, `Heat` | 被动治疗 |
| **L7d** | Medication | `NSAIDs`, `Muscle_Relaxants` | 药物 |
| **L7e** | Surgery | `Microdiscectomy`, `Fusion` | 手术 |

### L1 内部分类（subtype 体系）

| subtype | 示例 | 对应损伤 |
|:-------|:-----|:---------|
| `Flexion_compression` | `Lumbar_Flexion + Load` | Posterior disc herniation |
| `Shear` | `Lifting_with_round_back` | Spondylolisthesis |
| `Repetitive_low_load` | `Repeated_bending` | Disc degeneration / Creep |
| `Extension_compression` | `Backward_bending + Load` | Facet irritation |
| `Sustained_posture` | `Prolonged_sitting` | Disc nutrition deficit |

---

## 3. 数据库 Schema

数据库文件：`data/knowledge_base.db`

```sql
-- ========== 核心表 ==========

CREATE TABLE nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,          -- 英文标准名: Flexion_lumbar, Low_back_pain
    layer TEXT NOT NULL,                -- L0, L1, L2, L3, L4, L5, L6
    type TEXT,                          -- action / biomechanics / pathology / symptom /
                                        -- neurology / sign / imaging / intervention /
                                        -- medication / surgery / prognosis / anatomy /
                                        -- risk_factor / grading_level
    description TEXT,                   -- 简要描述（英文）
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    relation TEXT NOT NULL,             -- causes / treats / contraindicated_for /
                                        -- indicated_for / associated_with / prevents /
                                        -- increases / decreases / precedes / treated_by
    confidence REAL DEFAULT 0.8,        -- 0-1
    source_ref TEXT,                    -- 指南来源（如 "NICE_NG59_2023"）
    evidence TEXT,                      -- 原文证据摘要（英文，20-50字）
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (source_id) REFERENCES nodes(id),
    FOREIGN KEY (target_id) REFERENCES nodes(id)
);

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,                 -- 段落原文
    source TEXT NOT NULL,               -- 文献标识（如 "NICE_NG59_2023_ch3"）
    node_id INTEGER,                   -- 关联的概念节点（可为 NULL）
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

-- ========== 别名映射表（中英文+同义词） ==========

CREATE TABLE aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL,
    language TEXT NOT NULL,             -- 'zh' / 'en' / 'zh_synonym'
    display_name TEXT NOT NULL,         -- 中文："腰痛" / 英文："Low_back_pain" / 同义词："下背痛"
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
CREATE INDEX idx_aliases_display ON aliases(display_name);

-- ========== 日志表（可选，用于审计） ==========

CREATE TABLE inference_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_input TEXT,
    entities_found TEXT,                -- JSON
    graph_paths_found TEXT,             -- JSON
    chunks_retrieved TEXT,              -- JSON
    soap_output TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ========== 索引 ==========

CREATE INDEX idx_nodes_layer ON nodes(layer);
CREATE INDEX idx_edges_relation ON edges(relation);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_chunks_node ON chunks(node_id);
```

---

## 4. 模块接口定义

### 4.1 `entity_extractor.py`（`src/extraction/entity_extractor.py`）— 规则实体抽取

```python
def extract_entities(text: str) -> list[dict]:
    """
    输入：患者描述文本（中文，如"弯腰时腰痛，放射到小腿，直腿抬高40°"）
    输出：[{"name": "Flexion_lumbar", "layer": "L0", "value": None, "negated": False},
           {"name": "Low_back_pain", "layer": "L3", "value": None, "negated": False},
           {"name": "Radiating_pain", "layer": "L3", "value": None, "negated": False},
           {"name": "SLR_40deg_mild", "layer": "L4", "value": 40, "negated": False}]

    实现：
    1. 加载 dictionary（YAML）：中文词 → 英文节点名
    2. 对每个匹配做否定检测：检查前5个词是否有否定词
    3. 对匹配结果做分度映射：发现数值 → 映射到分级节点
    4. 返回实体列表
    """
```

### 4.2 `entity_normalizer`（`src/knowledge_graph/repository.py`）— 实体标准化

实体标准化功能内置于 `repository.py` 中，通过 `aliases` 表查询实现。

```python
def resolve_entities(raw_entities: list[dict]) -> list[dict]:
    """
    输入：entity_extractor 的输出
    输出：已映射到标准节点名的实体列表

    实现：
    1. 通过 aliases 表将中文/变体 → 标准英文节点名
    2. 对 negated=True 的实体标记排除
    3. 去重（同节点出现多次只保留一次）
    """

def get_grading_indicator(indicator: str, value: float) -> str | None:
    """
    输入：指标名（"SLR"），数值（40）
    输出：分级节点名（"SLR_40deg_mild"）或 None

    阈值映射表内置于函数或 config.yaml 中。
    """
```

### 4.3 `path_retriever.py`（`src/knowledge_graph/path_retriever.py`）— 图谱路径查询

```python
def find_paths(
    start_nodes: list[str],
    path_type: str = "mechanism",
    max_depth: int = 3,
    forbidden_nodes: list[str] | None = None
) -> list[list[dict]]:
    """
    输入：起始节点名列表，路径类型，最大深度
    输出：[[{"node": "Flexion_lumbar", "layer": "L0", "rel": None},
             {"node": "Disc_shear_force", "layer": "L1", "rel": "causes"},
             {"node": "Disc_herniation", "layer": "L2", "rel": "causes"},
             {"node": "Nerve_root_compression", "layer": "L3", "rel": "causes"}], ...]

    实现：
    1. 从 SQLite 读取所有 edges（带 relation 白名单过滤）
    2. 构建 NetworkX DiGraph
    3. 对每个 start_node，调用 nx.all_simple_paths(G, start, None, cutoff=max_depth)
    4. 对每条路径做：
       a. 层级单调性校验（不回退超过1级）
       b. path_type 过滤：mechanism → 终点 layer ≤3；intervention → 终点 layer ≥5
       c. 禁忌节点过滤
    5. 返回合法路径列表
    """

# 关系白名单（硬编码在函数中，未来可移到 config）
ALLOWED_RELATIONS_MECHANISM = {"causes", "increases", "decreases", "precedes",
                                "associated_with", "prevents"}
ALLOWED_RELATIONS_INTERVENTION = {"treats", "contraindicated_for", "indicated_for",
                                   "treated_by", "prevents"}

# 层级单调性校验（简单实现，从第 1 层起不能回退超过 1 级）
def check_layer_validity(layers: list[int]) -> bool:
    for i in range(1, len(layers)):
        if layers[i] < layers[i-1] - 1:
            return False
    return True
```

### 4.4 `graph_searcher.py`（`src/retrieval/graph_searcher.py`）— 图谱路径检索

```python
def retrieve_paths(
    entity_nodes: list[str],
    path_type: str = "mechanism",
    max_depth: int = 3
) -> list[list[dict]]:
    """
    封装 path_retriever.find_paths 的结果，增加缓存和日志。
    输入：实体节点名列表，路径类型
    输出：路径列表（同 path_retriever 格式）
    """
```

### 4.5 `chunk_searcher.py`（`src/retrieval/chunk_searcher.py`）— 向量文献检索

```python
def retrieve(
    node_ids: list[int],
    query_text: str,
    top_k: int = 3,
    fallback: bool = True
) -> list[dict]:
    """
    输入：图谱命中节点 ID 列表，原始查询文本
    输出：[{"text": "...", "source": "...", "node_id": ..., "score": 0.89}, ...]

    实现：
    1. 取 node_ids 关联的所有 chunks
    2. 用 embedder 对 query_text 编码
    3. 在限定 chunk 子集中做 FAISS 搜索（graph-steered）
    4. 如果命中 < top_k 且 fallback=True → 全库 FAISS 补充
    5. 返回 top_k 结果
    """
```

### 4.6 `soap_generator.py`（`src/generation/soap_generator.py`）— SOAP 生成

```python
def fill_template(state: AgentState) -> str:
    """
    代码执行模板填充，不调 LLM。
    输入：AgentState
    输出：带占位的 SOAP 草稿（中文）
    """

def llm_polish(draft: str, paths: list, chunks: list) -> str:
    """
    输入：SOAP 草稿，图谱路径，chunks
    输出：最终 SOAP 报告（中文，带证据标记）

    实现：
    1. 构建 LLM prompt（见 prompt_templates.py）
    2. 调用 DeepSeek API（JSON 模式, temperature=0.2）
    3. jsonschema 校验输出
       字段必须包含：subjective, objective, assessment, plan, evidence
    4. 校验失败 → 重试（max 2 次）
    5. 校验成功 → 渲染为中文文本报告
    """
```

### 4.7 `orchestrator.py`（`src/orchestrator.py`）— 主流程

```python
@dataclass
class AgentState:
    user_input: str
    demo_mode: bool = True
    entities: list = None           # [{"name": "Flexion_lumbar", "layer": "L0", "value": None, "negated": False}]
    grading_factors: list = None    # [{"indicator": "SLR", "level": "mild", "node": "SLR_40deg_mild"}]
    diagnosis: list = None          # ★ 新增 [{"suggests": "Discogenic_Pain", "confidence": 0.8, "mechanism_path": [...]}]
    path_type: str = "mechanism"    # "mech_path" | "diag_path" | "inter_path"
    graph_paths: list = None        # [[{"node": "...", "layer": "...", "rel": "..."}, ...], ...]
    chunks: list = None             # [{"text": "...", "source": "...", "node_id": ...}]
    soap_draft: str = None
    soap_report: str = None


def run_pipeline(user_input: str, demo_mode: bool = True) -> AgentState:
    """
    主流程：输入 → 输出，返回完整 state（每步都可调试查看）。
    """
    state = AgentState(user_input=user_input, demo_mode=demo_mode)

    # Step 1: 实体抽取
    if demo_mode:
        state.entities = entity_extractor.extract_entities(user_input)
    else:
        state.entities = json.loads(user_input)  # 结构化输入

    # Step 2: 实体标准化
    state.entities = repository.resolve_entities(state.entities)

    # Step 3: 诊断逻辑匹配 ★ 新增
    symptom_nodes = [e["name"] for e in state.entities if e.get("layer") in ("L4", "L5")]
    if symptom_nodes:
        state.diagnosis = diagnostic_matcher.match(symptom_nodes)

    # Step 4: 图谱查询
    start_nodes = [e["name"] for e in state.entities if not e.get("negated")]
    state.graph_paths = path_retriever.find_paths(
        start_nodes,
        path_type=state.path_type,
        forbidden_nodes=config.FORBIDDEN_NODES
    )

    # Step 5: RAG 检索（图谱引导）
    if state.graph_paths:
        node_ids = list({node["node_id"]
                        for path in state.graph_paths
                        for node in path})
        state.chunks = chunk_searcher.retrieve(node_ids, user_input)

    # Step 6: SOAP 生成
    state.soap_draft = soap_generator.fill_template(state)
    state.soap_report = soap_generator.llm_polish(state.soap_draft,
                                                    state.graph_paths,
                                                    state.chunks)

    return state
```

---

## 5. AgentState 数据流

```
        字段                    由谁写入              由谁读取
 ┌───────────────────┬────────────────────────┬──────────────────────┐
 │ user_input        │ 外部调用者              │ entity_extractor     │
 │ demo_mode         │ 外部调用者              │ entity_extractor     │
 │ entities          │ entity_extractor        │ repository           │
 │ grading_factors   │ entity_extractor        │ repository           │
 │ entities(标准化后)│ repository              │ diagnostic_matcher  │
 │ diagnosis         │ diagnostic_matcher       │ soap_generator      │ ← ★
 │ path_type         │ 外部/ config            │ path_retriever       │
 │ graph_paths       │ path_retriever          │ soap_generator       │
 │ chunks            │ chunk_searcher          │ soap_generator       │
 │ soap_draft        │ soap_generator.fill     │ soap_generator.llm   │
 │ soap_report       │ soap_generator.llm      │ 外部调用者           │
 └───────────────────┴────────────────────────┴──────────────────────┘
```

---

## 6. 路径约束规则

| 约束 | 实现方式 | 等级 |
|:----:|:--------:|:----:|
| 关系类型白名单 | `ALLOWED_RELATIONS_MECH_PATH` / `_DIAG_PATH` / `_INTER_PATH` | ✅ 必须 |
| 深度限制 | `max_depth=3（mech_path）/ max_depth=2（inter_path）` | ✅ 必须 |
| 层级单调性 | `check_layer_validity()` | ✅ 建议 |
| 路径类型分治 | `mech_path` (L0→L4) / `diag_path` (L4/L5→L6) / `inter_path` (L6→L7) | ✅ 必须 |
| 禁忌节点过滤 | `forbidden_nodes` 列表 | ⚠️ 可选 |
| 循环检测 | NetworkX `all_simple_paths` 自动去重 | ✅ 自动 |
| 证据等级过滤 | `edges.confidence > min_confidence` | ⏳ 未来 |

---

## 7. 诊断逻辑层（Diagnostic Logic Layer）

> 设计理由：临床推理的核心不是"A causes B"的事实罗列，而是
> "症状+体征 → 推断机制 → 验证假设"的模式识别过程。
> 没有这一层，系统只能回答"这是什么"，不能回答"这是为什么"。

### 7.1 定位

诊断逻辑层位于 **L4（症状）+ L5（体征/检查）→ L2/L3（病理/机制）** 之间。
它不存储"知识"，而是存储**推理规则**。

### 7.2 规则表示

```json
{
  "pattern": ["Flexion_Pain", "Sitting_Intolerance", "SLR_Positive"],
  "suggests": "Discogenic_Pain",
  "mechanism_path": ["Flexion_Compression", "Annulus_Tear", "Disc_Herniation"],
  "confidence": 0.8,
  "source_ref": "McGill_2007_Ch3"
}
```

### 7.3 诊断规则表

```sql
CREATE TABLE diagnostic_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,               -- JSON数组: 触发的症候群
    suggests TEXT NOT NULL,              -- 推断结论（L2/L3 节点名）
    mechanism_path TEXT,                 -- JSON数组: 完整机制链
    confidence REAL DEFAULT 0.7,
    source_ref TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 7.4 示例规则

| 症候群 (L4+L5) | 推断 (L2) | 机制链 | Confidence |
|:--------------|:---------|:-------|:---------:|
| `Flexion_Pain + Sitting_Intolerance + SLR_Positive` | `Discogenic_Pain` | Flexion_Compression → Annulus_Tear → Disc_Herniation | 0.8 |
| `Extension_Pain + Walking_Intolerance + Facet_Tenderness` | `Facet_Joint_Syndrome` | Extension_Compression → Facet_Impingement → Facet_Irritation | 0.75 |
| `Shear_Pain + Instability_Clutch + Sit_to_stand_Pain` | `Segmental_Instability` | Shear_Load → Ligamentous_Injury → Instability | 0.7 |
| `Night_Pain + Morning_Stiffness + Non_mechanical` | `Red_Flag` | — | 0.5 |

### 7.5 执行逻辑（MVP 简化版）

```python
def match_diagnosis(symptoms: list[str], signs: list[str]) -> list[dict]:
    """
    输入：患者 L4 症状 + L5 体征节点名列表
    输出：匹配的诊断规则（按 confidence 降序排列）
    实现：
    1. 从 diagnostic_rules 表读取所有规则
    2. 计算每条的 Overlap: |pattern ∩ (symptoms ∪ signs)| / |pattern|
    3. 只返回 Overlap ≥ 0.6 的规则
    4. 按 confidence × overlap 排序
    """
```

---

## 8. 中英文语言策略

```
知识图谱内部：英文标准名
  └─ nodes.name = "Flexion_lumbar", "Low_back_pain", "SLR_40deg_mild"

aliases 表映射：
  └─ node_id=1, language='zh', display_name='腰椎屈曲'
  └─ node_id=1, language='zh_synonym', display_name='弯腰'
  └─ node_id=1, language='en', display_name='Flexion_lumbar'

用户输入：中文 → entity_extractor + aliases → 英文节点名
图谱推理：全程英文节点名，不受语言影响
SOAP 输出：aliases 表取 language='zh' 渲染为中文
证据溯源：edges.source_ref 保留原文标识，evidence 保留英文摘要
```

---

## 9. Config 结构

```yaml
# config.yaml — Clinical Reasoning Agent 配置

medical:
  # 数据库
  db_path: "data/knowledge_base.db"
  faiss_index: "data/faiss_index/"

  # 图谱查询
  graph:
    max_depth: 3
    forbidden_nodes: ["Surgery", "Epidural_injection"]
    min_confidence: 0.5
    mech_path_max_end_layer: 4          # mech_path 型路径终点不超过 L4 (症状)
    diag_path_max_end_layer: 6          # diag_path 型终点 L6 (诊断逻辑)
    inter_path_max_depth: 2             # inter_path 型路径深度不超过 2

  # 关系白名单（按路径类型分三组）
  relations:
    mech_path: ["causes", "increases", "decreases", "precedes", "prevents"]
    diag_path: ["indicates", "suggests", "associated_with"]
    inter_path: ["treats", "contraindicated_for", "indicated_for", "treated_by", "prevents"]

  # 诊断逻辑
  diagnosis:
    min_overlap: 0.6                    # 症候群匹配最低覆盖率

  # RAG
  rag:
    top_k: 3
    fallback_enabled: true
    embedder_model: "all-MiniLM-L6-v2"
    embedder_dim: 384

  # LLM
  llm:
    model: "deepseek-chat"
    temperature: 0.2
    max_tokens: 2048
    retry_max: 2

  # 分度阈值（分级节点映射）
  grading:
    SLR:                             # 直腿抬高试验
      mild: [30, 50]
      moderate: [50, 70]
      severe: [70, 100]
    VAS:                             # 疼痛评分
      mild: [1, 4]
      moderate: [4, 7]
      severe: [7, 10]

  # 演示模式
  demo:
    zh_to_en_dict_path: "dictionaries/zh_to_en.yaml"
    negation_words: ["无", "没有", "否认", "不伴", "阴性", "未及", "(-)"]
```

---

## 10. 依赖清单

```
# deploy/requirements.txt — Clinical Reasoning Agent 依赖
# 与 kg_system 共用基础依赖（numpy, pyyaml, requests）
# 额外新增：

networkx>=3.0              # 图路径查询（核心新增）
jsonschema>=4.0            # LLM 输出校验
sentence-transformers>=3.0  # 复用 kg_system
faiss-cpu>=1.7              # 复用 kg_system
PyMuPDF>=1.23.0             # 指南 PDF 抽取（已有）
pyyaml>=6.0                 # 配置（已有）
# DeepSeek API via requests（已有）
```

---

## 11. 文件清单与职责

```
clinical_reasoning_agent/
│
├── docs/                              ← 设计文档、架构定义、对话归档
│   ├── ARCHITECTURE_SPEC.md           ← 本文档 — 架构规范
│   ├── ARCHITECTURE_DECISIONS.md      ← 架构决策记录
│   ├── ARCHITECTURE_CONVERGENCE.md    ← 三家 AI 架构收敛过程
│   ├── CONTEXT.md                     ← 项目上下文总览
│   ├── SCENARIOS.md                   ← 场景设计参考
│   └── conversations/                 ← AI 对话归档
│
├── src/
│   ├── infrastructure/                ← 共享基础设施层（无业务逻辑）
│   │   ├── database.py                ← SQLite 通用连接与 CRUD
│   │   ├── embedder.py                ← sentence-transformers 封装
│   │   ├── vector_store.py            ← FAISS 索引管理
│   │   ├── llm_client.py              ← DeepSeek/Ollama 调用
│   │   └── config.py                  ← 配置加载（yaml+env）
│   │
│   ├── knowledge_graph/               ← 知识图谱层
│   │   ├── schema.sql                 ← 建表语句（上面 §3）
│   │   ├── models.py                  ← 节点/边/别名数据类
│   │   ├── repository.py              ← 图谱 CRUD + 实体标准化（aliases 映射）
│   │   └── path_retriever.py          ← NetworkX 路径查询（关系过滤+层级校验）
│   │
│   ├── extraction/                    ← 实体抽取
│   │   └── entity_extractor.py        ← 规则/词典实体抽取（否定检测+分度映射）
│   │
│   ├── retrieval/                     ← 检索管道
│   │   ├── graph_searcher.py          ← 图谱路径检索封装
│   │   └── chunk_searcher.py          ← 向量文献检索（FAISS）
│   │
│   ├── reasoning/                     ← 诊断逻辑层 ★ 新增
│   │   ├── diagnostic_matcher.py      ← 症状+体征 → 模式匹配 → 推断机制
│   │   └── diagnostic_rules.yaml      ← 诊断规则定义（演示场景数据）
│   │
│   ├── generation/                    ← 生成层
│   │   ├── prompt_templates.py        ← SOAP 提示词模板
│   │   └── soap_generator.py          ← 模板填充 + LLM 润色
│   │
│   └── orchestrator.py               ← 主流程（run_pipeline + AgentState）
│
├── notebooks/                         ← 演示 Notebook
├── tests/                             ← 测试目录
├── deploy/                            ← 部署文件
│   └── requirements.txt               ← 依赖（上面 §10）
│
├── .env.example                       ← 环境变量示例
├── .gitignore                         ← Git 忽略规则
├── config.yaml                        ← 项目配置模板
├── PROJECT_STRUCTURE.md               ← 项目结构说明
└── README.md                          ← 项目说明
```

---

## 12. 实现优先级

### Phase A：骨架（第1步，跑通单条链路）

| 文件 | 产出 | 依赖 |
|:----:|:----:|:----:|
| `src/knowledge_graph/schema.sql` | 建 data/knowledge_base.db | 无 |
| `src/knowledge_graph/repository.py` + `models.py` | 手工插入 1 条黄金路径（20节点+30边+5chunks） | schema.sql |
| `src/knowledge_graph/path_retriever.py` | `find_paths()` 返回路径 | repository |
| `src/generation/soap_generator.py` | `fill_template()` 模板填充 | 无 |
| `src/orchestrator.py` | `run_pipeline()` 走通写死输入 | 以上全部 |

**验证**：`python -c "from src.orchestrator import run_pipeline; print(run_pipeline('腰痛', demo_mode=True).soap_draft)"`

### Phase B：输入（第2步，演示模式可跑）

| 文件 | 产出 | 依赖 |
|:----:|:----:|:----:|
| `dictionaries/zh_to_en.yaml` | 20个中文→英文映射 | 无 |
| `src/extraction/entity_extractor.py` | `extract_entities()` 匹配中文输入 | zh_to_en.yaml |
| `src/knowledge_graph/repository.py` (resolve_entities) | `resolve_entities()` 标准化 | aliases 表数据 |

**验证**：`run_pipeline("弯腰时腰痛，放射到小腿")` 输出完整 SOAP

### Phase C：增强（第3步，精度提升）

| 文件 | 产出 | 依赖 |
|:----:|:----:|:----:|
| `src/retrieval/chunk_searcher.py` | 图谱引导的 FAISS 检索 | infrastructure embedder + vector_store |
| `src/generation/soap_generator.llm_polish()` | LLM 润色 | DeepSeek API |
| 分度逻辑 | SLR / VAS 分级映射 | config.yaml |

**验证**：`run_pipeline("直腿抬高40°，VAS 5分")` 输出含分级推理

### Phase D：展示（第4步，面试准备）

| 文件 | 产出 | 依赖 |
|:----:|:----:|:----:|
| `notebooks/example.ipynb` | 2个场景 Notebook | 以上全部 |
| README.md | 运行说明+架构图+免责声明 | 无 |
| 图谱扩展 | LLM 从第2份指南抽取更多数据 | extract_guideline.py |

**验证**：打开 Notebook → Run All → 看到 SOAP 输出