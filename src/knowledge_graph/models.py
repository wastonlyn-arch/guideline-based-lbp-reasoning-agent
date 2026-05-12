"""
知识图谱数据模型 — 节点/边/别名/诊断规则/分度指标数据类。

这些 dataclass 是整个项目的"公用契约"：
  - extraction 模块输出 EntityNode 列表
  - retrieval 模块操作 Relation/Path 数据
  - generation 模块消费推理路径

依赖规则: 本模块不依赖项目中任何其他模块（仅 Python 标准库）。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EntityNode:
    """知识图谱节点。"""
    name: str
    layer: str                                   # L0-L8
    type: str = "generic"                        # symptom, diagnosis, cause, intervention, exam
    subtype: str = ""                            # 细分类别: pain, exercise_therapy, mechanical_load
    description: str = ""
    is_core: bool = False
    id: Optional[int] = None
    aliases: list[str] = field(default_factory=list)


@dataclass
class Relation:
    """节点间关系边。"""
    source_id: int
    target_id: int
    relation: str                                # causes, treated_by, indicates, etc.
    confidence: float = 1.0
    source_ref: str = ""
    evidence: str = ""
    id: Optional[int] = None

    @property
    def source_name(self) -> Optional[str]:
        """来源节点名称（由 repository 填充后可用）。"""
        return getattr(self, "_source_name", None)

    @source_name.setter
    def source_name(self, value: str):
        self._source_name = value

    @property
    def target_name(self) -> Optional[str]:
        return getattr(self, "_target_name", None)

    @target_name.setter
    def target_name(self, value: str):
        self._target_name = value


@dataclass
class Alias:
    """节点别名（多语言/同义词）。"""
    node_id: int
    display_name: str
    language: str = "zh"
    is_preferred: bool = False
    id: Optional[int] = None


@dataclass
class Path:
    """推理路径（图谱检索结果）。"""
    nodes: list[EntityNode] = field(default_factory=list)
    edges: list[Relation] = field(default_factory=list)
    total_score: float = 0.0

    def to_text(self, separator: str = " → ") -> str:
        """将路径渲染为文本。"""
        if not self.nodes:
            return ""
        return separator.join(f"{n.name}[{n.layer}]" for n in self.nodes)

    def __len__(self) -> int:
        return len(self.nodes)


@dataclass
class DiagnosticRule:
    """诊断/推理规则（由指南抽取生成）。"""
    pattern: list[str]                           # 匹配模式节点名列表
    suggests: str                                # 建议的诊断/干预节点名
    mechanism_path: list[str]                    # 推理路径节点名列表
    confidence: float = 0.5
    category: str = "general"                    # diagnosis, treatment, referral
    id: Optional[int] = None


@dataclass
class GradingThreshold:
    """分度阈值。"""
    level: str                                   # 等级标识: action_limit, mild, moderate, severe
    range_desc: str = ""                         # 范围描述: NIOSH, 30-50, >50
    node_name: str = ""                          # 映射到的节点名


@dataclass
class GradingIndicator:
    """分度指标（用于数值到分级节点的映射）。"""
    name: str                                    # 指标名: Lumbar_Compression_Level, SLR_Angle
    thresholds: list[GradingThreshold] = field(default_factory=list)
    id: Optional[int] = None


@dataclass
class TermMapping:
    """术语映射（英文节点名 ↔ 中文术语）。"""
    node_name: str                               # 节点英文名（PascalCase）
    zh_term: str                                 # 中文术语
    layer: str                                   # L0-L8 层级
    node_type: str = "generic"
    node_subtype: str = ""
    description: str = ""
    id: Optional[int] = None
