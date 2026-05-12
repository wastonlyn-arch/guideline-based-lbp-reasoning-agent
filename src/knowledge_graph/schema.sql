-- ============================================================
-- clinical_reasoning_agent — 医学知识图谱 Schema
-- ============================================================
-- 层次 (L0-L8): S, C, R, I, Ix, Cx, Rc, Pd, Pr
-- ============================================================

-- 节点表（症状/体征、诊断、原因、干预等）
CREATE TABLE IF NOT EXISTS nodes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,           -- 节点名称（英文 PascalCase）
    layer       TEXT NOT NULL,                  -- L0-L8 层级标识
    type        TEXT NOT NULL DEFAULT 'generic', -- 节点类型: symptom, diagnosis, cause, intervention, exam, etc.
    subtype     TEXT DEFAULT '',                -- 细分类别: pain, exercise_therapy, mechanical_load, etc.
    description TEXT DEFAULT '',                -- 详细描述
    is_core     INTEGER DEFAULT 0,             -- 是否核心节点（1=是）
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer);
CREATE INDEX IF NOT EXISTS idx_nodes_type  ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_subtype ON nodes(subtype);

-- 边表（节点间关系）
CREATE TABLE IF NOT EXISTS edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   INTEGER NOT NULL REFERENCES nodes(id),
    target_id   INTEGER NOT NULL REFERENCES nodes(id),
    relation    TEXT NOT NULL,                  -- 关系类型: causes, treated_by, indicates, etc.
    confidence  REAL DEFAULT 1.0,              -- 置信度 (0-1)
    source_ref  TEXT DEFAULT '',               -- 证据来源（指南/文献引用）
    evidence    TEXT DEFAULT '',                -- 证据描述
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_unique ON edges(source_id, target_id, relation);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation);

-- 别名表（节点多语言/同义词映射）
CREATE TABLE IF NOT EXISTS aliases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id     INTEGER NOT NULL REFERENCES nodes(id),
    language    TEXT NOT NULL DEFAULT 'zh',     -- 语言: zh, en, ja, etc.
    display_name TEXT NOT NULL,                 -- 别名/同义词/外文名
    is_preferred INTEGER DEFAULT 0             -- 是否首选显示名
);

CREATE INDEX IF NOT EXISTS idx_aliases_node ON aliases(node_id);
CREATE INDEX IF NOT EXISTS idx_aliases_display ON aliases(display_name);

-- 文档块表（向量检索的源片段）
CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT NOT NULL,                  -- 文档片段内容
    source      TEXT NOT NULL,                  -- 来源文档标识
    node_id     INTEGER REFERENCES nodes(id),  -- 关联的节点（可为NULL）
    chunk_index INTEGER DEFAULT 0,             -- 片段在原文中的序号
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_node ON chunks(node_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source);

-- 诊断规则表（推理引擎规则）
-- pattern: JSON 数组字符串，如 '["Spinal_Hinge", "Back_Pain"]'
-- mechanism_path: JSON 数组字符串，如 '["Regional_Stiffness", "Single_Segment_Motion", "Pain"]'
CREATE TABLE IF NOT EXISTS diagnostic_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern         TEXT NOT NULL,              -- JSON 数组，匹配模式
    suggests        TEXT NOT NULL,              -- 建议的诊断/干预
    mechanism_path  TEXT DEFAULT '[]',          -- JSON 数组，推理路径（节点名列表）
    confidence      REAL DEFAULT 0.5,           -- 规则置信度
    category        TEXT DEFAULT 'general',     -- 规则类别: diagnosis, treatment, referral
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_rules_suggests ON diagnostic_rules(suggests);

-- 分度指标表（用于数值到分级节点的映射）
CREATE TABLE IF NOT EXISTS grading_indicators (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,           -- 指标名: Lumbar_Compression_Level, SLR_Angle
    created_at  TEXT DEFAULT (datetime('now'))
);

-- 分度阈值表
CREATE TABLE IF NOT EXISTS grading_thresholds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id    INTEGER NOT NULL REFERENCES grading_indicators(id),
    level           TEXT NOT NULL,              -- 等级标识: action_limit, mild, moderate, severe
    range_desc      TEXT DEFAULT '',            -- 范围描述: NIOSH, 30-50, >50
    node_name       TEXT NOT NULL,              -- 映射到的节点名
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_grading_thresholds_indicator ON grading_thresholds(indicator_id);

-- 术语映射表（英文节点名 ↔ 中文术语对照）
CREATE TABLE IF NOT EXISTS term_mapping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_name       TEXT NOT NULL REFERENCES nodes(name),
    zh_term         TEXT NOT NULL,                 -- 中文术语
    layer           TEXT NOT NULL,                 -- L0-L8 层级
    node_type       TEXT NOT NULL DEFAULT 'generic',
    node_subtype    TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(node_name, zh_term)
);

CREATE INDEX IF NOT EXISTS idx_term_mapping_node ON term_mapping(node_name);
CREATE INDEX IF NOT EXISTS idx_term_mapping_zh ON term_mapping(zh_term);

-- 推理日志表（审计追踪）
CREATE TABLE IF NOT EXISTS inference_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL,
    user_input          TEXT NOT NULL,
    entities_found      TEXT DEFAULT '[]',      -- JSON array
    graph_paths_found   TEXT DEFAULT '[]',      -- JSON array
    chunks_retrieved    TEXT DEFAULT '[]',      -- JSON array
    soap_output         TEXT DEFAULT '',         -- 生成的 SOAP 报告
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_inference_log_session ON inference_log(session_id);