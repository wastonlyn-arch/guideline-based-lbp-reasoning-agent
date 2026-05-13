# Architecture Laws — 分层架构单向依赖铁律

## paths: ["src/**/*.py"]

编辑 `src/` 下的 Python 代码时强制校验以下规则。

## 分层依赖（严格单向）

```
infrastructure  ←  knowledge_graph  ←  retrieval  ←  generation  ←  orchestrator
                        ↑                ↑
                    extraction       reasoning
```

## 各层红线

| 层 | 可导入 | 禁止导入 |
|----|--------|---------|
| `infrastructure/` | 无 | 任何其他 `src/` 模块 |
| `knowledge_graph/` | `infrastructure` | `extraction`, `reasoning`, `retrieval`, `generation` |
| `extraction/` | `infrastructure`, `knowledge_graph` | `reasoning`, `retrieval`, `generation` |
| `reasoning/` | `infrastructure`, `knowledge_graph`, `extraction`, `retrieval` | `generation`, `orchestrator` |
| `retrieval/` | `infrastructure`, `knowledge_graph` | `generation` |
| `generation/` | `infrastructure`, `retrieval`, `reasoning` | 直接操作数据库 |
| `orchestrator.py` | 全部 | 无 |

## 违反示例

```python
# ❌ 禁止：reasoning 层直接 import generation
from src.generation.report_generator import ReportGenerator

# ✅ 正确：reasoning 层只引用 infrastructure / knowledge_graph / extraction / retrieval
from src.infrastructure.database import Database
from src.knowledge_graph.graph import KnowledgeGraph
from src.extraction.entity_extractor import EntityExtractor
```

## 数据库访问红线

- SQL 查询仅允许在 `src/infrastructure/database.py` 中出现
- 业务层（`extraction/`, `reasoning/`, `retrieval/`, `generation/`, `orchestrator.py`）禁止构造 SQL 字符串
- 所有数据访问必须通过 `infrastructure/` 暴露的 repository/DAO 接口
- 如果新模块需要数据库访问，在 `infrastructure/` 中添加方法，不要在调用者中写 SQL

## 循环引用禁止

分层结构必须保持无环。如果某次导入会造成循环（A 导入 B 且 B 导入 A），必须重构：
- 将共享依赖抽取到 `infrastructure/`，或
- 通过构造函数/函数参数注入依赖，而非直接 import