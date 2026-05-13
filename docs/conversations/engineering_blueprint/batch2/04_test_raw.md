# Batch 2 · 04_test — 讨论原始记录
> 生成时间: 2026-05-14T06:57:40.800798
> 模型: primary=gemini-2.5-flash, critic=gpt-4.1-mini, convergence=deepseek-v4-flash
---
## Phase 1: 发散 — 各角色回答
### critic
1. **严重性**：High  
   **具体说明**：方案中提到的单元测试和集成测试依赖于 mock LLM 响应，但没有明确考虑流式（streaming）与非流式响应的差异。实际生产环境中，LLM 可能采用流式输出，若测试只模拟非流式响应，可能导致接口行为与真实环境不符，测试结果失真。  
   **修改建议**：增加针对流式响应的 mock 设计，模拟逐步返回数据的过程，确保测试覆盖流式和非流式两种交互模式。

2. **严重性**：Medium  
   **具体说明**：测试数据库使用的是内存 SQLite，但未明确说明数据库 schema 是否与生产环境完全一致。若 schema 有差异，测试覆盖的逻辑可能与生产环境不符，导致潜在问题未被发现。  
   **修改建议**：确保测试用的 SQLite schema 与生产数据库 schema 完全同步，或者采用迁移脚本自动生成测试环境数据库结构，避免人为维护不一致。

3. **严重性**：High  
   **具体说明**：测试方案缺少对错误路径的覆盖，如 LLM 超时、FAISS 检索无结果、实体识别失败等异常情况。这些是系统稳定性和健壮性的关键点，忽略测试会导致线上出现未预料的崩溃或错误处理不当。  
   **修改建议**：设计专门的异常模拟测试用例，覆盖各种错误场景，验证系统能否正确处理和恢复。

4. **严重性**：Medium  
   **具体说明**：没有提及并发测试策略。Streamlit 应用通常面向多用户并发访问，缺少并发测试可能导致竞态条件、状态污染或性能瓶颈未被发现。  
   **修改建议**：增加并发访问的集成测试，模拟多用户同时请求，检测共享资源的线程安全和状态隔离。

5. **严重性**：Low  
   **具体说明**：测试 fixture 生成脚本未提及维护策略。随着 schema 或业务逻辑变化，假数据可能过时，导致测试失效或误报。  
   **修改建议**：将 fixture 生成脚本纳入版本控制和持续集成流程，定期验证和更新，必要时编写针对 fixture 生成的单元测试。

6. **严重性**：Medium  
   **具体说明**：测试优先级未明确。建议先重点覆盖核心业务逻辑和错误处理路径，性能和并发测试可在基础功能稳定后再补充。当前策略未体现优先级，可能导致资源分散。  
   **修改建议**：制定明确的测试编写和执行优先级计划，将单元测试和关键异常路径测试放在首位，性能和压力测试作为后续阶段。

7. **严重性**：Medium  
   **具体说明**：测试之间是否完全隔离未说明。共享状态或全局变量若未清理，可能导致测试间相互影响，增加调试难度。  
   **修改建议**：确保每个测试用例独立执行，使用独立的上下文和清理机制，避免状态污染。

总结：当前测试策略在模拟真实环境的细节（流式响应、数据库 schema）、异常路径覆盖、并发测试和测试维护方面存在明显不足。建议针对这些问题进行补充和优化，以提升测试的有效性和可维护性。

### primary
好的，作为资深软件架构师，我将为您设计一份全面的测试策略，以确保 Clinical Reasoning Agent (MCRM) 项目的质量和稳定性。

---

## Clinical Reasoning Agent - MCRM 物理治疗临床推理教学辅助项目测试策略

### 1. 测试金字塔

我们将采用经典的测试金字塔模型，确保测试的效率和覆盖率。

-   **单元测试 (Unit Tests)**: 占测试总量的 **~70%**。
    -   **目标**: 验证单个函数、方法或类的独立行为是否符合预期。
    -   **特点**: 快速、隔离、易于编写和维护。
    -   **覆盖范围**: 核心业务逻辑、数据处理、算法实现。
    -   **依赖处理**: 严格 Mock 外部依赖。

-   **集成测试 (Integration Tests)**: 占测试总量的 **~20%**。
    -   **目标**: 验证模块之间、模块与外部依赖（如数据库、向量存储）之间的交互是否正确。
    -   **特点**: 相对较慢，但能发现模块间接口问题。
    -   **覆盖范围**: 数据库操作、API 客户端调用（Mock 外部服务响应）、组件间数据流。
    -   **依赖处理**: 使用 Fake 或小型化的真实依赖（如内存数据库、小样本文件）。

-   **端到端测试 (End-to-End Tests / E2E)**: 占测试总量的 **~10%**。
    -   **目标**: 模拟真实用户场景，验证整个系统从输入到输出的完整流程。
    -   **特点**: 最慢、最脆弱，但能发现系统级问题和用户体验问题。
    -   **覆盖范围**: 核心业务流程，如患者主诉输入到 SOAP 报告生成。
    -   **依赖处理**: 尽可能使用真实的外部依赖（或高度仿真的 Fake 服务），但 DeepSeek API 等不可控服务仍需 Mock。

**大致比例**: 单元测试 (70%) : 集成测试 (20%) : E2E 测试 (10%)

### 2. 每个模块的最小可测试单元

以下是每个模块需要测试的核心函数/方法及其输入输出样本：

```python
# tests/unit/test_entity_extractor.py
from src.extraction.entity_extractor import EntityExtractor

def test_extract_common_symptoms():
    extractor = EntityExtractor()
    text = "患者主诉：腰痛3月，伴右下肢麻木，无发热。"
    expected_output = [
        {"entity": "腰痛", "type": "symptom", "start": 6, "end": 8},
        {"entity": "3月", "type": "duration", "start": 8, "end": 10},
        {"entity": "右下肢麻木", "type": "symptom", "start": 13, "end": 18},
        {"entity": "发热", "type": "symptom", "start": 20, "end": 22, "negated": True}
    ]
    assert extractor.extract(text) == expected_output

# tests/unit/test_embedder.py
from src.infrastructure.embedder import Embedder

def test_embed_text_single():
    embedder = Embedder()
    text = "这是一个测试文本。"
    embedding = embedder.embed_text(text)
    assert len(embedding) == embedder.embedding_dim # 假设 embedding_dim 是模型输出维度
    assert isinstance(embedding, list) # 或 numpy.ndarray

# tests/unit/test_llm_client.py
from src.infrastructure.llm_client import LLMClient
from unittest.mock import patch

@patch('src.infrastructure.llm_client.DeepSeekClient') # 假设 DeepSeekClient 是实际的 API 客户端
def test_llm_client_generate_text(mock_deepseek_client):
    # Mock DeepSeekClient 的 chat 方法
    mock_deepseek_client.return_value.chat.return_value = {
        "choices": [{"message": {"content": "Mocked LLM response."}}]
    }
    client = LLMClient()
    prompt = "请总结以下内容："
    response = client.generate_text(prompt)
    assert response == "Mocked LLM response."
    mock_deepseek_client.return_value.chat.assert_called_once()

# tests/unit/test_repository.py
from src.knowledge_graph.repository import KnowledgeGraphRepository
from src.knowledge_graph.models import Node, Edge
import sqlite3

def test_add_and_get_node():
    conn = sqlite3.connect(':memory:') # 使用内存数据库
    repo = KnowledgeGraphRepository(conn)
    repo.initialize_db() # 创建表结构

    node = Node(id="N001", type="Symptom", name="腰痛")
    repo.add_node(node)
    retrieved_node = repo.get_node("N001")
    assert retrieved_node.name == "腰痛"

# tests/unit/test_path_retriever.py
from src.knowledge_graph.path_retriever import PathRetriever
import networkx as nx

def test_retrieve_shortest_paths():
    # 构造一个简单的图
    graph = nx.Graph()
    graph.add_edges_from([('A', 'B'), ('B', 'C'), ('A', 'D'), ('D', 'C')])
    retriever = PathRetriever(graph)

    paths = retriever.retrieve_paths(start_node='A', end_node='C', max_paths=2)
    expected_paths = [['A', 'B', 'C'], ['A', 'D', 'C']]
    # 注意：路径顺序可能不同，需要进行集合比较或排序后比较
    assert sorted(paths) == sorted(expected_paths)

# tests/unit/test_rule_engine.py
from src.reasoning.rule_engine import RuleEngine

def test_match_simple_rule():
    rules = [
        {"id": "R001", "conditions": ["symptom:腰痛", "duration:3月"], "conclusions": ["diagnosis:慢性腰痛"]},
        {"id": "R002", "conditions": ["symptom:发热"], "conclusions": ["diagnosis:感染"]}
    ]
    facts = {"symptom": ["腰痛"], "duration": ["3月"], "negated_symptom": ["发热"]}
    engine = RuleEngine(rules)
    matched_rules = engine.match_rules(facts)
    assert len(matched_rules) == 1
    assert matched_rules[0]["id"] == "R001"

# tests/unit/test_chunk_searcher.py
from src.retrieval.chunk_searcher import ChunkSearcher
import faiss
import numpy as np

def test_chunk_searcher_search():
    # 构造一个简单的 FAISS 索引
    dimension = 768
    index = faiss.IndexFlatL2(dimension)
    # 添加一些假数据
    data = np.random.rand(5, dimension).astype('float32')
    index.add(data)

    # 模拟 Embedder
    class MockEmbedder:
        def embed_text(self, text):
            return np.random.rand(dimension).astype('float32')

    searcher = ChunkSearcher(index, MockEmbedder())
    query_text = "测试查询"
    results = searcher.search(query_text, k=2)
    assert len(results) == 2
    assert isinstance(results[0], dict)
    assert "id" in results[0] and "score" in results[0] and "text" in results[0]

# tests/unit/test_soap_generator.py
from src.generation.soap_generator import SOAPGenerator
from unittest.mock import Mock

def test_soap_generator_generate():
    # Mock LLMClient
    mock_llm_client = Mock()
    mock_llm_client.generate_text.return_value = "润色后的SOAP内容"

    generator = SOAPGenerator(mock_llm_client)
    patient_data = {
        "subjective": "患者自述腰痛3月",
        "objective": "查体：右膝关节压痛",
        "assessment": "诊断：慢性腰痛",
        "plan": "建议：理疗"
    }
    soap_report = generator.generate_soap(patient_data)
    assert "润色后的SOAP内容" in soap_report
    mock_llm_client.generate_text.assert_called_once()

# tests/integration/test_orchestrator_flow.py
from src.orchestrator import ClinicalReasoningOrchestrator
from unittest.mock import patch, MagicMock

@patch('src.infrastructure.llm_client.LLMClient')
@patch('src.retrieval.chunk_searcher.ChunkSearcher')
@patch('src.knowledge_graph.repository.KnowledgeGraphRepository')
@patch('src.extraction.entity_extractor.EntityExtractor')
def test_orchestrator_full_flow_integration(
    mock_entity_extractor, mock_kg_repo, mock_chunk_searcher, mock_llm_client
):
    # 模拟各个模块的返回值
    mock_entity_extractor.return_value.extract.return_value = [
        {"entity": "腰痛", "type": "symptom"}
    ]
    mock_kg_repo.return_value.find_paths.return_value = [
        ["腰痛", "肌肉劳损", "治疗方案A"]
    ]
    mock_chunk_searcher.return_value.search.return_value = [
        {"id": "C001", "text": "腰痛的常见原因是肌肉劳损。"}
    ]
    mock_llm_client.return_value.generate_text.return_value = "Mocked SOAP Report"

    # 假设 Orchestrator 构造函数需要这些依赖
    orchestrator = ClinicalReasoningOrchestrator(
        entity_extractor=mock_entity_extractor.return_value,
        kg_repository=mock_kg_repo.return_value,
        chunk_searcher=mock_chunk_searcher.return_value,
        llm_client=mock_llm_client.return_value,
        # 其他依赖也需要 Mock 或 Fake
        embedder=MagicMock(),
        vector_store=MagicMock(),
        path_retriever=MagicMock(),
        rule_engine=MagicMock(),
        confidence_aggregator=MagicMock(),
        soap_generator=MagicMock(return_value=MagicMock(generate_soap=lambda x: "Mocked SOAP Report"))
    )

    patient_complaint = "患者主诉：腰痛"
    soap_report = orchestrator.run(patient_complaint)

    assert "Mocked SOAP Report" in soap_report
    mock_entity_extractor.return_value.extract.assert_called_once_with(patient_complaint)
    # 验证其他关键模块是否被调用
    # mock_kg_repo.return_value.find_paths.assert_called_once()
    # mock_chunk_searcher.return_value.search.assert_called_once()
    # mock_llm_client.return_value.generate_text.assert_called_once()

```

### 3. Mock/Fake 策略

我们将根据依赖的性质和测试层级，采用不同的 Mock/Fake 策略。

-   **LLM 调用 (DeepSeek API)**:
    -   **策略**: 使用 `unittest.mock.patch` 或 `pytest-mock` 库来模拟 `LLMClient.generate_text()` 方法。
    -   **实现**: 返回预定义的 JSON 结构或字符串。
    -   **示例 (伪代码)**:
        ```python
        # tests/conftest.py 或测试文件中
        import pytest
        from unittest.mock import MagicMock

        @pytest.fixture
        def mock_llm_client():
            mock = MagicMock()
            mock.generate_text.return_value = "这是一个来自Mock LLM的SOAP报告。"
            return mock

        # 在测试中使用
        def test_some_function_with_llm(mock_llm_client):
            # 注入 mock_llm_client 到需要它的组件
            # ...
            result = some_component.process(..., llm_client=mock_llm_client)
            assert "Mock LLM" in result
            mock_llm_client.generate_text.assert_called_once()
        ```
    -   **固定返回**: 可以从 `tests/fixtures/mock_llm_responses.json` 文件中加载不同的预定义响应。

-   **FAISS 索引**:
    -   **单元测试**:
        -   **策略**: 直接在测试代码中创建 `faiss.IndexFlatL2` 对象，并添加少量随机或特定构造的向量。
        -   **实现**: 使用 `numpy` 生成向量，`faiss.add()` 添加。
        -   **示例**: 见 `test_chunk_searcher_search` 单元测试。
    -   **集成测试**:
        -   **策略**: 预构建一个包含少量真实数据的 FAISS 索引文件，并将其作为 fixture 加载。
        -   **实现**: `faiss.read_index("tests/fixtures/small_faiss.index")`。

-   **图谱数据 (SQLite + NetworkX)**:
    -   **SQLite 数据库**:
        -   **策略**: 使用 `:memory:` 数据库连接进行单元和大部分集成测试。
        -   **实现**: `sqlite3.connect(':memory:')`。在测试 setup 中调用 `KnowledgeGraphRepository.initialize_db()` 创建表结构，并插入少量假数据。
        -   **示例**: 见 `test_add_and_get_node` 单元测试。
        -   **持久化小图谱**: 对于需要更复杂数据场景的集成测试，可以预构建一个 `tests/fixtures/small_kg.db` 文件，并在测试中复制到临时路径或直接连接。
    -   **NetworkX 图**:
        -   **策略**: 直接在测试代码中构造 `networkx.Graph` 对象，或从 `tests/fixtures/mock_networkx_graph.gml` (或 JSON) 文件加载。
        -   **实现**: `nx.Graph()`, `graph.add_edges_from(...)`。
        -   **示例**: 见 `test_retrieve_shortest_paths` 单元测试。

### 4. 测试数据管理

所有测试数据都将集中管理在 `tests/fixtures/` 目录下。

-   **目录结构**:
    ```
    tests/
    ├── fixtures/
    │   ├── small_kg.db                 # 小型 SQLite 知识图谱数据库
    │   ├── small_faiss.index           # 小型 FAISS 向量索引文件
    │   ├── mock_llm_responses.json     # 模拟 LLM 响应的 JSON 文件
    │   ├── mock_networkx_graph.gml     # 模拟 NetworkX 图的 GML 文件
    │   └── e2e_test_cases.json         # 端到端测试用例的输入/预期输出
    ├── unit/
    │   └── ...
    ├── integration/
    │   └── ...
    └── e2e/
        └── ...
    ```

-   **需要哪些 fixture**:
    1.  **`small_kg.db`**: 包含少量节点、边和 chunk 的 SQLite 数据库。用于 `knowledge_graph.repository` 和 `retrieval.graph_searcher` 的集成测试。
    2.  **`small_faiss.index`**: 包含少量向量和对应 chunk ID 的 FAISS 索引。用于 `retrieval.chunk_searcher` 的集成测试。
    3.  **`mock_llm_responses.json`**: 存储不同 DeepSeek API 调用场景的模拟响应。例如：
        ```json
        {
            "summarize_symptoms": "患者主诉：腰痛3月，伴右下肢麻木。",
            "generate_soap_template": "Subjective: {{s}} Objective: {{o}} Assessment: {{a}} Plan: {{p}}",
            "refine_soap_final": "最终润色后的SOAP报告。"
        }
        ```
    4.  **`mock_networkx_graph.gml`**: 一个包含少量节点和边的 GML 格式文件，用于 `knowledge_graph.path_retriever` 的集成测试。
    5.  **`e2e_test_cases.json`**: 包含患者主诉输入和预期 SOAP 报告关键部分的 JSON 数组。

-   **fixture 生成脚本 vs 手动维护**:
    -   **小型、静态数据 (如 `mock_llm_responses.json`, `mock_networkx_graph.gml`)**: 优先手动维护，确保可读性和精确性。
    -   **结构化数据 (如 `small_kg.db`, `small_faiss.index`)**:
        -   **初期**: 可以手动创建少量数据，然后通过脚本导出。
        -   **后期**: 随着数据复杂性增加，可以编写 Python 脚本 (`scripts/generate_fixtures.py`) 来生成这些文件。例如，脚本可以从 CSV 文件读取数据，然后构建 SQLite 数据库和 FAISS 索引。这有助于保持数据的一致性和可重复性。

### 5. 关键场景的 E2E 测试

E2E 测试将验证整个推理管线的核心功能。

-   **文件路径**: `tests/e2e/test_full_pipeline.py`
-   **测试数据**: 从 `tests/fixtures/e2e_test_cases.json` 加载。

```python
# tests/e2e/test_full_pipeline.py
import pytest
import json
from src.orchestrator import ClinicalReasoningOrchestrator
from unittest.mock import patch, MagicMock

# 假设 Orchestrator 及其所有依赖都已正确初始化，
# 并且外部服务（如 DeepSeek）已被 Mock 或 Fake
# 在实际 E2E 中，我们会尽量使用真实的内部组件，只 Mock 外部 API

@pytest.fixture(scope="module")
def e2e_orchestrator():
    # 这里需要一个更真实的 Orchestrator 实例，但 DeepSeek 仍需 Mock
    # 我们可以创建一个专门用于 E2E 的配置，指向小型化的真实依赖
    # 例如，使用内存SQLite，小型FAISS索引文件等
    with patch('src.infrastructure.llm_client.LLMClient') as MockLLMClient:
        # 配置 Mock LLM 客户端的响应
        mock_llm_instance = MockLLMClient.return_value
        mock_llm_instance.generate_text.side_effect = [
            "患者自述腰痛3月，伴右下肢麻木，无发热。", # 模拟实体抽取后的总结
            "查体：右膝关节压痛，浮髌试验阳性。", # 模拟客观检查总结
            "评估：初步诊断为慢性腰痛，可能伴有神经根受压。", # 模拟评估
            "计划：建议进行MRI检查，并开始物理治疗，包括牵引和核心肌群训练。" # 模拟计划
        ]
        # 假设其他内部依赖（如DB, FAISS）使用小型真实fixture
        # 这里为了简化，仍使用 MagicMock，但在实际E2E中会是真实实例
        orchestrator = ClinicalReasoningOrchestrator(
            entity_extractor=MagicMock(),
            kg_repository=MagicMock(),
            chunk_searcher=MagicMock(),
            llm_client=mock_llm_instance,
            embedder=MagicMock(),
            vector_store=MagicMock(),
            path_retriever=MagicMock(),
            rule_engine=MagicMock(),
            confidence_aggregator=MagicMock(),
            soap_generator=MagicMock(return_value=MagicMock(generate_soap=lambda x: f"S:{x['subjective']}\nO:{x['objective']}\nA:{x['assessment']}\nP:{x['plan']}"))
        )
        # 进一步配置内部组件的mock行为以模拟真实数据流
        orchestrator.entity_extractor.extract.return_value = [
            {"entity": "腰痛", "type": "symptom"},
            {"entity": "3月", "type": "duration"},
            {"entity": "右下肢麻木", "type": "symptom"}
        ]
        orchestrator.kg_repository.find_paths.return_value = [
            ["腰痛", "椎间盘突出", "神经根受压"]
        ]
        orchestrator.chunk_searcher.search.return_value = [
            {"text": "椎间盘突出常引起腰痛和下肢麻木。"}
        ]
        yield orchestrator

@pytest.fixture(scope="module")
def e2e_test_cases():
    with open("tests/fixtures/e2e_test_cases.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.e2e
@pytest.mark.parametrize("case", e2e_test_cases())
def test_clinical_reasoning_e2e_scenarios(e2e_orchestrator, case):
    patient_complaint = case["input"]
    expected_output_keywords = case["expected_output_keywords"]

    soap_report = e2e_orchestrator.run(patient_complaint)

    # 验证 SOAP 报告是否包含预期的关键词
    for keyword in expected_output_keywords:
        assert keyword in soap_report, f"Expected keyword '{keyword}' not found in SOAP report for input: {patient_complaint}"

# tests/fixtures/e2e_test_cases.json 示例
[
    {
        "id": "E2E_001",
        "input": "患者主诉：腰痛3月，伴右下肢麻木，无发热。",
        "expected_output_keywords": ["腰痛", "右下肢麻木", "慢性腰痛", "神经根受压", "MRI检查", "物理治疗"]
    },
    {
        "id": "E2E_002",
        "input": "患者主诉：右膝关节疼痛2周，活动受限，无红肿发热。查体：右膝关节压痛，浮髌试验阳性。",
        "expected_output_keywords": ["右膝关节疼痛", "活动受限", "压痛", "浮髌试验阳性", "膝关节炎", "半月板损伤", "休息", "冰敷"]
    },
    {
        "id": "E2E_003",
        "input": "患者主诉：左肩关节疼痛1个月，夜间加重，活动时疼痛。查体：左肩外展受限，冈上肌压痛。",
        "expected_output_keywords": ["左肩关节疼痛", "夜间加重", "外展受限", "冈上肌压痛", "肩周炎", "肌腱炎", "康复训练"]
    },
    {
        "id": "E2E_004_unrecognized",
        "input": "患者主诉：我感觉身体不舒服，说不上来哪里疼。",
        "expected_output_keywords": ["无法提供精确推理", "建议进一步检查"] # 预期优雅降级或通用提示
    }
]
```

### 6. CI/CD 集成

我们将使用 GitHub Actions 来自动化测试流程，确保代码质量和快速反馈。

-   **pytest 配置 (`pytest.ini`)**:

    ```ini
    # pytest.ini
    [pytest]
    minversion = 6.0
    addopts = -ra -v --strict-markers --cov=src --cov-report=term-missing --cov-fail-under=80
    testpaths = tests
    markers =
        unit: Marks a test as a unit test.
        integration: Marks a test as an integration test.
        e2e: Marks a test as an end-to-end test.
        llm_integration: Marks a test that interacts with the actual LLM API (DeepSeek).
    timeout = 300 # 默认超时时间，单位秒
    ```
    -   `--cov=src`: 测量 `src/` 目录下的代码覆盖率。
    -   `--cov-report=term-missing`: 在终端显示未覆盖的代码行。
    -   `--cov-fail-under=80`: 如果总代码覆盖率低于 80%，则测试失败。
    -   `timeout`: 防止测试长时间运行。

-   **GitHub Actions 触发条件**:

    -   **`on: push`**:
        -   `branches: [ main ]`: 每次推送到 `main` 分支时，运行所有测试 (单元、集成、E2E)。
        -   `branches: [ feature/* ]`: 每次推送到特性分支时，运行单元和集成测试。
    -   **`on: pull_request`**:
        -   `branches: [ main ]`: 每次向 `main` 分支提交 PR 时，运行单元和集成测试。
    -   **`on: schedule`**:
        -   `cron: '0 0 * * *'` (每天午夜运行): 触发 `nightly_llm_tests`。

-   **GitHub Actions 工作流 (`.github/workflows/ci.yml`)**:

    ```yaml
    # .github/workflows/ci.yml
    name: CI/CD Pipeline

    on:
      push:
        branches:
          - main
          - 'feature/*' # 针对特性分支
      pull_request:
        branches:
          - main
      schedule:
        - cron: '0 0 * * *' # 每天午夜运行

    jobs:
      unit_and_integration_tests:
        name: Unit & Integration Tests
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python 3.11
            uses: actions/setup-python@v4
            with:
              python-version: "3.11"
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install pytest pytest-cov pytest-mock networkx faiss-cpu sentence-transformers
          - name: Run Unit and Integration Tests
            run: |
              # 运行所有非 E2E 和非 LLM_integration 的测试
              pytest -m "not e2e and not llm_integration"

      e2e_tests:
        name: End-to-End Tests
        runs-on: ubuntu-latest
        needs: unit_and_integration_tests # 确保单元/集成测试通过后才运行 E2E
        if: github.event_name == 'push' && github.ref == 'refs/heads/main' || github.event_name == 'pull_request' && github.base_ref == 'main'
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python 3.11
            uses: actions/setup-python@v4
            with:
              python-version: "3.11"
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install pytest pytest-cov pytest-mock networkx faiss-cpu sentence-transformers
          - name: Run E2E Tests
            env:
              # E2E 测试可能需要真实的 DeepSeek API Key，但这里我们仍建议 Mock
              # DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
            run: |
              pytest -m e2e

      nightly_llm_integration_tests:
        name: Nightly LLM Integration Tests
        runs-on: ubuntu-latest
        if: github.event_name == 'schedule'
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python 3.11
            uses: actions/setup-python@v4
            with:
              python-version: "3.11"
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install pytest pytest-cov pytest

---
## Phase 2: 收敛 — final_decision
采用primary提供的详细测试策略框架（包括测试金字塔、每个模块的最小可测试单元、Mock/Fake策略、测试数据管理、E2E测试场景及CI/CD集成），同时强制纳入critic指出的关键缺失：1) 增加流式响应的模拟与测试；2) 补充异常路径覆盖（如LLM超时、FAISS无结果等）；3) 在CI工作流中增加并发测试（在基础测试通过后执行）；4) 明确测试优先级顺序（单元->异常路径->E2E->并发）；5) 所有测试用例必须独立，利用pytest的fixture隔离机制。最终方案既保留了primary的完整结构，又修复了critic识别的高风险漏洞，优于单一方案。

### consensus
- 应采用测试金字塔模型（单元测试占比最高，集成测试次之，端到端测试最低）。
- 需要为外部依赖（LLM API、FAISS、数据库等）设计Mock/Fake策略。
- 集成测试中使用内存SQLite数据库，避免对生产数据库的依赖。
- 测试数据应集中管理，并考虑维护策略（版本控制、定期更新）。
- 应集成到CI/CD流水线中自动化执行。
- 端到端测试应覆盖核心业务流程（如患者主诉到SOAP报告生成）。

### divergences
- 是否需要对LLM流式响应进行专项测试: majority=方案中未明确区分流式与非流式响应，仅使用通常的Mock方法。 / minority=必须增加针对流式响应的测试，否则可能与真实行为不符。 → 采纳少数派意见，在Mock LLM时增加流式模式的模拟，覆盖逐步返回数据的场景。
- 异常路径测试的覆盖范围: majority=异常路径测试虽然重要但在方案中未具体设计。 / minority=必须设计专门的异常模拟用例（如LLM超时、FAISS检索无结果、实体识别失败等），避免线上崩溃。 → 在集成和单元测试中增加异常场景的用例，验证错误处理逻辑。
- 并发测试的必要性与时机: majority=并发测试未被纳入当前方案。 / minority=应考虑并发测试，但优先级可放在基础功能稳定之后。 → 将并发测试作为后续阶段，并在测试计划中明确优先级顺序。
- 测试优先级与执行顺序: majority=未明确制定测试编写优先级。 / minority=应优先覆盖核心业务逻辑和关键异常路径，然后再补充性能和并发测试。 → 在测试计划中明确优先级：单元测试优先，异常路径测试紧随其后，性能与并发测试放后。
- 测试隔离性（是否明确清理共享状态）: majority=未说明测试间是否隔离。 / minority=应确保每个测试用例独立执行，使用独立上下文和清理机制。 → 在测试框架中强制要求隔离性，使用fixture的scope或cleanup钩子。

### risk_notes
- 流式响应的实现细节可能随LLM提供商变化，Mock需要维护更新。
- 异常路径测试可能增加维护成本，需平衡覆盖率与效率。
- 并发测试可能引入不稳定因素，需要稳定的测试环境。
- 数据库schema同步若自动化不足，可能导致测试与生产环境脱节。