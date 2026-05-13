# Cline 配置体系系统性指南

> 针对 **clinical_reasoning_agent** 项目编写  
> 适用场景：医疗 AI 分层架构 + 数据安全 + 知识图谱查询

---

## 目录

1. [Rules（规则）](#1-rules规则)
2. [Workflows（工作流）](#2-workflows工作流)
3. [Hooks（钩子）](#3-hooks钩子)
4. [Skills（技能）](#4-skills技能)
5. [MCP（Model Context Protocol）](#5-mcp-model-context-protocol)
6. [优先级与作用域](#6-优先级与作用域)
7. [最小可生效配置组合](#7-最小可生效配置组合)

---

## 1. Rules（规则）

### 1.1 核心概念

Rules 是 Cline 的**行为铁律**，告诉 AI Agent 什么能做、什么不能做、怎么做。  
每条规则本质上是一段 Markdown 文本，Cline 在每次交互时都会读取并遵守。

### 1.2 配置位置

| 作用域 | 路径 | 说明 |
|--------|------|------|
| **全局级** | `C:\Users\<用户名>\.cline\rules\*.md` | 所有项目共享 |
| **项目级** | `<project-root>\.clinerules\*.md` | 仅当前项目生效 |
| 旧版兼容 | `<project-root>\.clinerules` (单文件) | 已不推荐 |

### 1.3 Rules 文件格式

> ⚠️ **重要更正**：Cline Rules 文件使用 **`.md`** 扩展名，**不需要** YAML frontmatter。

#### 始终生效的规则（无条件）

```markdown
# 规则标题
规则内容...
```

不包含 `# paths` 或 `---` 的 `.md` 文件，在每次任务开始时都会被加载。

#### 条件生效的规则（仅匹配特定路径时）

```markdown
# 规则标题

## paths: ["src/**/*.py"]

这些规则仅在编辑 `src/` 下的 Python 文件时生效。
```

- `## paths:` 后面跟一个 JSON 数组（glob 模式）
- 可以使用多个 `## paths:` 条目匹配不同路径集
- 匹配的文件变更后，这些规则在后续工具调用中持续生效

#### 支持的 glob 语法

| 模式 | 匹配 | 不匹配 |
|------|------|--------|
| `*.py` | `foo.py` | `src/foo.py` |
| `src/**/*.py` | `src/foo.py`, `src/a/b/bar.py` | `foo.py` |
| `src/*.py` | `src/foo.py` | `src/a/foo.py` |

#### 规则如何被检测/加载

Cline 的规则加载机制：
1. **文件监视（File Watcher）**：Cline 在每次启动时扫描 `.clinerules/` 目录，读取所有 `.md` 文件
2. **无 frontmatter**：官方格式不需要 `---` 分隔的 frontmatter。如果你在 `.md` 文件中写了 `---`，Cline 会将其视为普通 Markdown 内容
3. **路径限制**：只有在变更的文件匹配 `## paths:` 中指定的 glob 时，该规则才会被加载到当前会话
4. **合并读取**：所有符合条件的 `.md` 文件会被合并到一个上下文中，不存在"同名覆盖"的概念

### 1.4 优先级关键

1. **项目级规则覆盖全局级规则**：如果项目 `.clinerules/` 和全局 `~/.cline/rules/` 中存在同路径文件，项目版本优先
2. **条件规则仅在匹配路径时加载**：不匹配 `## paths:` 的规则在当前会话中**不会被使用**
3. **路径匹配 vs 无条件**：不带 `## paths:` 的规则始终加载；带路径的规则仅当编辑匹配文件时加载
4. **所有规则合并到一个上下文**：不存在"文件 A 覆盖文件 B"的概念，所有规则共同组成指令集

### 1.5 可复制的规则模板

#### 模板 A：架构铁律（保护分层依赖不被破坏）

文件名：`.clinerules\architecture-laws.md`

```markdown
# Architecture Laws — 分层架构单向依赖铁律

## paths: ["src/**/*.py"]

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
| `generation/` | `infrastructure`, `retrieval`, `reasoning` | 直接操作数据库 |

## 数据库访问红线

- SQL 查询仅允许在 `src/infrastructure/database.py` 中出现
- 业务层禁止构造 SQL 字符串
```

#### 模板 B：医疗数据安全红线

文件名：`.clinerules\data_safety.md`

```markdown
# Data Safety Rules

1. **Do NOT commit secrets**: API keys, passwords, tokens must go in `.env`, never in code or config.yaml.
2. **SQLite safety**: Use parameterized queries for all SQL. No string formatting of `WHERE` clauses.
3. **No production data in dev**: Use synthetic/sample data for development and testing.
4. **Clean up temp files**: Temporary artifacts should be gitignored or explicitly deleted after use.
```

#### 模板 C：代码风格（带 glob 限制）

文件名：`.clinerules\coding_style.md`

```markdown
# Coding Style Rules

## paths: ["src/**/*.py"]

## Docstrings

Use Google-style docstrings for all public classes and functions.

## Type annotations

All function parameters and return values must have type annotations.

## Prohibited patterns

- ❌ `from module import *`
- ❌ Bare `except:` without specifying exception type
- ❌ `print()` in production code (use `logging`)
- ❌ Global variables for configuration (use Config dataclass)
- ❌ Circular imports (enforced by module dependency rules)
```

---

## 2. Workflows（工作流）

### 2.1 核心概念

Workflows 是 Cline 的高级功能，允许你定义**多步骤的工作流模板**。  
每步可以指定：角色、输入、输出、检查点，Cline 会按步骤顺序执行，并在每步完成后等待确认。

### 2.2 配置位置

| 类型 | 路径 | 说明 |
|------|------|------|
| 全局 Workflow | `~/.cline/workflows/*.md` | 所有项目可用 |
| 项目 Workflow | `<project-root>/.clinerules/workflows/*.md` | 仅当前项目 |

### 2.3 Workflow 文件格式

```markdown
---
name: 工作流名称
description: 简短描述
---

## Step 1: 步骤名称
### Role
你的角色（例如 "architect"、"code reviewer"）

### Instructions
在此步骤中你需要完成的具体工作描述

## Step 2: 下一步
### Role
### Instructions
...
```

> ⚠️ 注意：Workflows 使用 YAML frontmatter（`---` 包裹），这与 Rules 文件不同。Workflows 需要 `name` 和 `description` 字段。

### 2.4 可复制的 Workflow 模板

#### 我的项目：SOAP 开发工作流

文件名：`.clinerules\workflows\soap-dev-workflow.md`

```markdown
---
name: SOAP Report 开发工作流
description: 从需求到 SOAP 报告生成的完整开发流程
---

## Step 1: 需求分析与设计
### Role
architect

### Instructions
1. 阅读 `docs/CONTEXT.md` 了解项目背景
2. 阅读 `docs/SCENARIOS.md` 了解当前开发阶段
3. 检查 `docs/DEVELOPMENT_LOG.md` 待办池
4. 输出：本次开发的设计文档摘要
5. **等待用户确认后进入下一步**

## Step 2: 实现核心逻辑
### Role
developer

### Instructions
1. 严格遵循分层依赖规则
2. 所有公开函数添加 Google 风格 docstring 和类型注解
3. 使用 `logging` 模块，不用 print
4. 输出：实现代码（一个模块或一个功能点）
5. **等待用户确认后进入下一步**
```

---

## 3. Hooks（钩子）

### 3.1 核心概念

Hooks 是 Cline 的**事件触发器**，在特定时机自动执行脚本或检查。  
Hooks 在 VS Code 设置中配置，不在 `.clinerules/` 目录下。

### 3.2 支持哪些 Hook 类型

| Hook 类型 | VS Code 配置键 | 触发时机 | Windows 兼容性 |
|-----------|---------------|---------|---------------|
| Pre-tool | `cline.hooks.preTool` | 在 AI 调用任何工具**之前** | ✅ |
| Post-tool | `cline.hooks.postTool` | 在 AI 调用工具**完成之后** | ✅ |
| Pre-commit | `cline.hooks.preCommit` | 在 AI 执行 git commit **之前** | ✅ |

Hook 脚本的运行方式由 `command` + `args` 决定，支持：
- `"command": "powershell"` — 执行 PowerShell 脚本
- `"command": "python"` — 执行 Python 脚本
- Hook 支持占位符：`${workspaceFolder}` 会替换为当前项目根目录

### 3.3 配置位置

Hook 在 VS Code `settings.json` 中配置，可以是：
- **全局设置**：`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
- **工作区设置**：`.vscode/settings.json`

推荐放在**全局设置**中，因为你可能希望所有项目都默认启用 Hooks。

### 3.4 可复制的 Hook 配置

```json
// VS Code settings.json（全局）
{
  "cline.hooks": {
    "preTool": [],
    "postTool": [
      {
        "name": "检查跨层导入",
        "command": "python",
        "args": [
          "${workspaceFolder}/.clinerules/hooks/check_imports.py",
          "${file}"
        ],
        "enabled": true,
        "scope": "project"
      }
    ],
    "preCommit": [
      {
        "name": "敏感文件扫描",
        "command": "powershell",
        "args": [
          "-NoProfile",
          "-File",
          "${workspaceFolder}\\.clinerules\\hooks\\pre_commit_scan.ps1"
        ],
        "enabled": true,
        "scope": "project"
      }
    ]
  }
}
```

#### Hook 脚本 A：检查跨层导入违规（Post-tool）

文件名：`.clinerules\hooks\check_imports.py`

```python
"""Post-tool Hook: 检查修改的文件是否有跨层导入违规"""
import re
import sys
from pathlib import Path

LAYER_DEPENDENCIES = {
    "infrastructure": set(),
    "knowledge_graph": {"infrastructure"},
    "extraction": {"infrastructure", "knowledge_graph"},
    "reasoning": {"infrastructure", "knowledge_graph", "extraction", "retrieval"},
    "retrieval": {"infrastructure", "knowledge_graph"},
    "generation": {"infrastructure", "retrieval", "reasoning"},
}

def check_file(filepath: Path) -> list[str]:
    content = filepath.read_text(encoding="utf-8")
    violations = []
    imports = re.findall(r"^\s*from\s+src\.(\w+)", content, re.MULTILINE)
    imports += re.findall(r"^\s*import\s+src\.(\w+)", content, re.MULTILINE)
    
    for part in filepath.parts:
        if part in LAYER_DEPENDENCIES:
            current_layer = part
            allowed = LAYER_DEPENDENCIES[current_layer]
            for dep in imports:
                if dep != current_layer and dep not in allowed:
                    violations.append(
                        f"❌ {filepath}: 禁止 {current_layer} 导入 {dep}"
                    )
            break
    return violations

if __name__ == "__main__":
    changed_files = sys.argv[1:] if len(sys.argv) > 1 else []
    all_violations = []
    for f in changed_files:
        p = Path(f)
        if p.suffix == ".py":
            all_violations.extend(check_file(p))
    
    if all_violations:
        print("\n".join(all_violations))
        print("⚠️  请在提交前修复以上导入违规")
        sys.exit(1)
    else:
        print("✅ 导入检查通过")
```

#### Hook 脚本 B：敏感文件提交拦截（Pre-commit）

文件名：`.clinerules\hooks\pre_commit_scan.ps1`

```powershell
# Pre-commit Hook: 扫描敏感文件
param()

$sensitive_patterns = @(
    '\.env$',
    '\.env\.local$',
    '\.sqlite$',
    '\.db$',
    '__pycache__',
    '\.pytest_cache',
    'node_modules'
)

$changes = git diff --cached --name-only 2>$null
if (-not $changes) {
    Write-Host "✅ 无暂存文件更改"
    exit 0
}

$issues = @()

foreach ($file in $changes) {
    foreach ($pattern in $sensitive_patterns) {
        if ($file -match $pattern) {
            $issues += "⚠️  敏感文件将被提交: $file"
        }
    }
}

if ($issues.Count -gt 0) {
    Write-Host "`n❌ 提交被拒绝:"
    $issues | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host "✅ 敏感文件检查通过"
```

---

## 4. Skills（技能）

### 4.1 核心概念

Skills 是 Cline 的**可复用能力包**，将一组领域知识、提示词模板、验证逻辑打包成一个可调用的"技能"。  
你可以将 Skills 理解为 Cline 的"插件"，让 AI 在不重新学习的前提下，掌握特定领域的专业知识。

### 4.2 配置位置

| 类型 | 路径 | 说明 |
|------|------|------|
| 全局 Skill | `~/.cline/skills/*.md` | 所有项目可用 |
| 项目 Skill | `<project-root>/.clinerules/skills/*.md` | 仅当前项目 |

### 4.3 Skill 文件格式

```markdown
---
name: 技能名称
description: 简短描述
---

# 技能名称

## Context（上下文）
技能生效前需要了解的项目背景信息

## Instructions（指令）
技能激活后 AI 应该如何行动

## Output Format（输出格式）
技能输出的标准格式模板

## Validation（验证规则）
如何验证输出是否符合预期
```

> ⚠️ Skills 使用 YAML frontmatter，需要 `name` 和 `description` 字段（与 Workflows 类似，与 Rules 不同）。

### 4.4 如何触发 Skill

Skills 通过以下方式触发：
- **用户手动选择**：在 Cline 聊天的 VS Code 界面中，通过 `#` 菜单选择 Skill
- **用户直接在聊天中提及**：例如"帮我生成一个 SOAP 报告"可能会被 Skill 名称匹配

注意：Skills 目前**不支持** `triggers` 字段自动激活。Skill 需要用户主动选择。

### 4.5 可复制的 Skill 模板

#### Skill A：SOAP 报告生成

文件名：`.clinerules\skills\soap-generator.md`

```markdown
---
name: SOAP报告生成
description: 从患者主诉生成结构化 SOAP 报告
---

# SOAP Report Generation Skill

## Context

SOAP 是医疗记录的标准化格式：
- **S**ubjective：患者主诉（患者自述症状、病史）
- **O**bjective：客观检查数据（体征、实验室结果、影像学）
- **A**ssessment：评估与诊断（鉴别诊断、推理依据）
- **P**lan：治疗计划（药物、检查、随访）

本项目使用知识图谱 + LLM 的混合架构：
1. 实体抽取 → 图谱检索 → 向量检索 → LLM 生成
2. 图谱路径提供推理依据（M-rules）
3. LLM 消费推理路径生成自然语言报告

## Instructions

1. 首先完成实体抽取（检查 `src/extraction/` 是否已实现）
2. 执行图谱检索（`src/knowledge_graph/`）获取相关医学知识路径
3. 执行向量检索（`src/retrieval/`）获取文献支持
4. 调用 LLM 生成 SOAP 格式报告（`src/generation/`）
5. 验证：
   - 报告包含所有 4 个部分（S/O/A/P）
   - 无患者真实姓名（使用 session_id 替代）
   - 推理路径有图谱证据支撑（引用 M-rule）

## Output Format

```markdown
## SOAP 报告 — Patient #[session_id]

### Subjective
[患者主诉摘要]

### Objective
[客观检查数据]

### Assessment
[诊断评估 + 推理依据]
- 图谱路径：[引用]

### Plan
[治疗计划]
```

## Validation

- [ ] 包含 S/O/A/P 四个部分
- [ ] 无 PHI（患者身份信息）
- [ ] 每个评估有推理路径引用
- [ ] Plan 部分可执行（具体药物/检查名称）
```

---

## 5. MCP（Model Context Protocol）

### 5.1 核心概念

MCP 是 Cline **连接外部工具和服务的标准协议**。  
通过 MCP，Cline 可以直接操作数据库、文件系统、搜索网页、读写文件和调用外部 API，而不仅仅是文本聊天。

MCP 本质是一个**本地服务器**，Cline 通过标准化的 JSON-RPC 协议与它通信：

```
Cline (LLM)  ↔  MCP Client  ↔  MCP Server  ↔  外部工具（数据库、API、文件系统）
```

### 5.2 配置位置

MCP 服务器在 VS Code 的全局设置或 `.vscode/mcp.json` 中配置：

| 位置 | 路径 | 生效范围 |
|------|------|---------|
| 工作区文件 | `<project-root>/.vscode/mcp.json` | 仅当前项目 |
| 全局设置 | `C:\Users\<用户名>\.cline\mcp.json` | 所有项目 |

两者可以共存，同名 server 时项目级覆盖全局级。

### 5.3 MCP JSON 配置格式

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_KEY": "${env:API_KEY}"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

参数说明：
- `command`：启动服务器的可执行文件（`python`, `node`, `npx`, `uvx` 等）
- `args`：传递给命令的参数数组
- `env`：环境变量（可选），支持 `${env:VAR_NAME}` 从系统环境变量读取
- `disabled`：是否禁用（可选，默认 `false`）
- `autoApprove`：工具列表，这些工具调用时不需用户确认（可选）

### 5.4 可复制的 MCP 配置

#### MCP A：知识图谱查询（自定义 Python MCP Server）

`.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "kg-query-mcp": {
      "command": "python",
      "args": [".clinerules/mcp/kg_mcp_server.py"],
      "disabled": false,
      "autoApprove": ["kg_query", "m_rule_lookup"]
    }
  }
}
```

MCP Server 代码（`.clinerules/mcp/kg_mcp_server.py`）：

```python
"""
MCP Server: 知识图谱查询接口
运行方式：cline 自动启动，通过 MCP 协议通信
"""
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parents[3] / "data" / "knowledge_base.db"


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "kg_query",
                    "description": "查询知识图谱中的疾病-症状关系",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "disease": {"type": "string", "description": "疾病名称"},
                            "max_depth": {"type": "integer", "description": "查询深度", "default": 3}
                        },
                        "required": ["disease"]
                    }
                },
                {
                    "name": "m_rule_lookup",
                    "description": "查询 M-rule 规则详情",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string", "description": "规则 ID"}
                        },
                        "required": ["rule_id"]
                    }
                }
            ]
        }
    
    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        try:
            if tool_name == "kg_query":
                cursor = conn.execute(
                    """SELECT * FROM pathways WHERE disease = ? LIMIT 50""",
                    (arguments["disease"],)
                )
                results = [dict(row) for row in cursor.fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]}
            
            elif tool_name == "m_rule_lookup":
                cursor = conn.execute(
                    """SELECT * FROM m_rules WHERE rule_id = ?""",
                    (arguments["rule_id"],)
                )
                result = cursor.fetchone()
                if result:
                    return {"content": [{"type": "text", "text": json.dumps(dict(result), ensure_ascii=False, indent=2)}]}
                return {"content": [{"type": "text", "text": f"Rule {arguments['rule_id']} not found"}]}
        finally:
            conn.close()
    
    return {"error": f"Unknown method: {method}"}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e)}), flush=True)
```

#### MCP B：SQLite 数据库只读查询

```json
{
  "mcpServers": {
    "sqlite-mcp": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "d:\\cline_control\\clinical_reasoning_agent\\data\\knowledge_base.db"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

> 注意：此工具只能用于**只读查询**（SELECT）。所有写操作（INSERT/UPDATE/DELETE）必须通过项目的 `knowledge_graph/` 层，以保障数据一致性。

---

## 6. 优先级与作用域

### 6.1 配置优先级（高 → 低）

```
  高优先级                         低优先级
  ─────────────────────────────────────────
    会话指令  >  项目Rules  >  全局Rules  >  MCP配置  >  Skills/Workflows
    (当前对话)   (项目级规则)   (全局规则)    (工具连接)   (需手动触发)
```

### 6.2 详细优先级规则

| 配置类型 | 优先级 | 说明 |
|---------|--------|------|
| **会话内用户指令** | 🔴 最高 | "这次忽略分层规则" — 当前对话临时覆盖所有 Rules |
| **项目 Rules (.clinerules/)** | 🟠 次高 | 覆盖同路径全局规则文件 |
| **全局 Rules (~/.cline/rules/)** | 🟡 中高 | 无项目级覆盖时生效 |
| **项目 Hooks (.vscode/settings.json)** | 🟢 中 | 触发后独立执行，不覆盖 Rules |
| **MCP 配置** | 🔵 低 | 仅决定可用工具，不改变 AI 行为逻辑 |
| **Skills / Workflows** | 🟣 参考级 | 仅在用户主动选择/触发时生效，不强制 |

### 6.3 冲突解决规则

| 场景 | 结果 |
|------|------|
| 全局 rules 说"用 pip"，项目 rules 说"用 conda" | **项目 rules 胜出** |
| Rules 说"必须参数化查询"，Hooks 也检查同一件事 | 共同生效（Rules 指导行为，Hooks 执行检查） |
| Skill 说"SOAP 分四段"，Workflow Step 说"SOAP 分三段" | **Workflow 胜出**（Workflow 是用户显式选择的） |
| 项目 `.vscode/mcp.json` 和全局 `mcp.json` 定义了同名 server | **项目级覆盖全局级** |

### 6.4 作用域说明

```
作用域       配置位置                             生效范围
────────────────────────────────────────────────────────────────
全局级       ~/.cline/rules/*.md                 所有项目
             ~/.cline/mcp.json
             ~/.cline/skills/*.md
             VS Code 全局 settings.json 中的 cline.hooks

项目级       <project>/.clinerules/*.md           仅当前项目
             <project>/.clinerules/skills/*
             <project>/.clinerules/workflows/*
             <project>/.vscode/mcp.json
             <project>/.vscode/settings.json

会话级       当前聊天窗口中的手动指令              仅当前对话
             `#` 激活的 Skill
```

---

## 7. 最小可生效配置组合

以下配置组合覆盖了你的项目核心需求，复制粘贴即可使用：

### 7.1 文件结构

```
clinical_reasoning_agent/
├── .clinerules/
│   ├── architecture-laws.md       # [新增] 架构铁律（paths: src/**/*.py）
│   ├── coding_style.md            # [转换] 代码风格（paths: src/**/*.py）
│   ├── core_workflow.md           # [转换] 核心工作流（paths: src/**/*.py）
│   ├── data_safety.md             # [转换] 数据安全（无条件加载）
│   ├── machine_profile.md         # [转换] 机器档案（无条件加载）
│   ├── project_context.md         # [转换] 项目上下文（无条件加载）
│   ├── skills/
│   │   └── soap-generator.md      # [新增] SOAP 技能
│   ├── workflows/
│   │   └── soap-dev-workflow.md   # [新增] 开发工作流
│   ├── mcp/
│   │   └── kg_mcp_server.py       # [新增] MCP 图谱查询服务器
│   └── hooks/
│       ├── check_imports.py       # [新增] 导入检查 Hook (Post-tool)
│       └── pre_commit_scan.ps1    # [新增] 敏感文件扫描 (Pre-commit)
└── .vscode/
    ├── mcp.json                   # [新增] MCP 服务器注册
    └── settings.json              # [如需] Hook 注册（见下方说明）
```

### 7.2 快速安装

```powershell
# 进入项目目录
cd d:\cline_control\clinical_reasoning_agent

# 创建所有子目录
New-Item -ItemType Directory -Force -Path ".clinerules/skills", ".clinerules/workflows", ".clinerules/hooks", ".clinerules/mcp", ".vscode"

# 检查项目 Rules 是否生效
# ✅ 下一次启动 Cline 会话时自动生效
```

### 7.3 VS Code 全局 Hooks 配置（需手动添加）

打开 VS Code 全局设置 JSON（`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"），添加：

```jsonc
// VS Code 全局 settings.json — 所有项目共享
{
  // ... 现有设置 ...

  "cline.hooks": {
    "postTool": [
      {
        "name": "检查跨层导入",
        "command": "python",
        "args": [
          "${workspaceFolder}/.clinerules/hooks/check_imports.py",
          "${file}"
        ],
        "enabled": true,
        "scope": "project"
      }
    ],
    "preCommit": [
      {
        "name": "敏感文件扫描",
        "command": "powershell",
        "args": [
          "-NoProfile",
          "-File",
          "${workspaceFolder}\\.clinerules\\hooks\\pre_commit_scan.ps1"
        ],
        "enabled": true,
        "scope": "project"
      }
    ]
  }
}
```

> **注意**：Hooks 当前必须在全局 VS Code 设置中注册，不能放在项目 `.vscode/settings.json` 中（除非你使用工作区设置）。推荐放全局，因为 `"scope": "project"` 已确保它只对当前项目生效。

### 7.4 启动核对清单

每次开始新会话时，在第一条消息中包含以下提示：

```
我会遵循 clinical_reasoning_agent 项目的配置：
1. 📐 architecture-laws：严格分层单向依赖
2. 🔒 data_safety：参数化查询 + 无 PHI 泄漏
3. 🏭 machine_profile：Windows + conda + RTX 4060
4. 📋 core_workflow/coding_style：代码规范
5. 🧪 MCP：使用知识图谱查询服务器（只读）
6. 💡 需要生成 SOAP 报告时激活对应的 Skill
```

---

## 附录 A：配置对比速查表

| 配置项 | 扩展名 | Frontmatter | 加载方式 | 文件位置 |
|--------|--------|-------------|---------|---------|
| **Rules** | `.md` | ❌ 不需要 | 自动加载（每次任务开始） | `.clinerules/*.md` |
| **Workflows** | `.md` | ✅ `name`, `description` | 用户在选择器中点击 | `.clinerules/workflows/*.md` |
| **Skills** | `.md` | ✅ `name`, `description` | 用户通过 `#` 菜单选择 | `.clinerules/skills/*.md` |
| **Hooks** | `.py` / `.ps1` | — | 由 VS Code settings.json 触发 | `.clinerules/hooks/*` |
| **MCP** | `.json` / `.py` | — | 自动启动（配置在 `.vscode/mcp.json`） | `.vscode/mcp.json` |

## 附录 B：术语对照

| 术语 | 英文 | 说明 |
|------|------|------|
| 规则 | Rules | AI 行为约束和指导原则 |
| 工作流 | Workflows | 多步骤、有序的 AI 执行流程 |
| 钩子 | Hooks | 在特定时机自动触发的脚本检查 |
| 技能 | Skills | 封装了领域知识的可复用能力包 |
| MCP | Model Context Protocol | 连接外部工具的标准协议 |

## 附录 C：常见问题

**Q: `.mdc` 和 `.md` 扩展名哪个正确？**  
A: **`.md`** 是官方支持的扩展名。`.mdc` 文件不会被 Cline 读取。

**Q: 为什么我的 Rules 文件不生效？**  
A: 检查以下三点：① 文件名是否为 `.md` 而非 `.mdc`；② 是否放在正确的目录（`.clinerules/`）；③ 如果使用 `## paths:`，确认 glob 模式匹配了正在编辑的文件。

**Q: Hooks 和 Rules 有什么区别？**  
A: Rules 是静态的指令集（告诉 AI "应该这样做"），Hooks 是动态的脚本执行（在事后自动检查"有没有做对"）。两者互补，不冲突。

**Q: 配置了 MCP 但 Cline 不启动服务器？**  
A: 确认 JSON 格式正确（无尾逗号），`command` 和 `args` 中的路径使用反斜杠（`\\`）或正斜杠。重启 VS Code 尝试。

**Q: Skills 中的 `triggers` 字段为什么不生效？**  
A: `triggers` 是早期版本的功能，当前 Cline 版本 Skills 需要用户通过 `#` 菜单**手动选择**才能激活。

---

> 📅 编写日期：2026-05-13  
> 📌 适用于 Cline 最新版本