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
4. 输出：本次开发的设计文档摘要（架构变更、接口设计、数据流）
5. **等待用户确认后进入下一步**

## Step 2: 实现核心逻辑
### Role
developer

### Instructions
1. 严格遵循分层依赖规则（检查 `.clinerules/architecture-laws.md`）
2. 为所有公开函数添加 Google 风格 docstring 和类型注解
3. 使用 `logging` 模块，不用 print
4. 数据安全规则：所有患者信息输入输出必须脱敏
5. 输出：实现代码（一个模块或一个功能点）
6. **等待用户确认后进入下一步**

## Step 3: 单元测试与集成测试
### Role
tester

### Instructions
1. 为 Step 2 新增的代码编写 pytest 测试
2. 测试覆盖范围：
   - 正常输入路径
   - 边界条件（空输入、特殊符号）
   - 错误处理（数据库异常、LLM 超时）
3. 运行 `python -m pytest tests/ -v` 确认通过
4. 输出：测试代码 + 测试运行结果
5. **等待用户确认后进入下一步**

## Step 4: 验证 SOAP 报告输出
### Role
qa

### Instructions
1. 运行端到端 demo 脚本（如果有）
2. 验证生成的 SOAP 报告格式符合标准（Subjective → Objective → Assessment → Plan）
3. 验证无 PHI 泄漏
4. 输出：验证结果 + 问题列表（如果有）
5. **等待用户确认后进入下一步**

## Step 5: 更新文档与 Git 提交
### Role
documenter

### Instructions
1. 在 `docs/DEVELOPMENT_LOG.md` 追加记录
   - 内容模板：**做了什么 → 产出物 → 卡住问题 → 决策**
2. 更新状态看板
3. 执行 git commit 前检查清单（确认无 `.env`、`*.db`、`__pycache__` 被提交）
4. `git add . && git commit -m "<scope>: <描述>"`
5. 输出：commit hash + 本次完成摘要 + 下一步建议
6. **停止，等待用户确认**