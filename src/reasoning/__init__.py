"""
推理引擎层 — v0.3 MVP
=====================
提供基于规则的可解释推理引擎，包括：
- rule_engine: 规则匹配引擎（M-rule 驱动）
- path_builder: 可解释推理路径构建
- confidence: 置信度聚合

依赖规则: 可依赖 infrastructure、knowledge_graph、retrieval，不可依赖 generation 或 orchestrator。
"""