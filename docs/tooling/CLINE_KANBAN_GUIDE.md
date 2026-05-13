# Cline Kanban 使用指南

> 基于官方文档整理，面向中文开发者  
> 关键术语首次出现时标注英文原文

---

## 目录

1. [概述](#1-概述)
2. [快速开始](#2-快速开始)
3. [核心工作流](#3-核心工作流)
4. [功能详解](#4-功能详解)
5. [远程访问](#5-远程访问)
6. [附录](#6-附录)

---

## 1. 概述

### 1.1 什么是 Cline Kanban

Cline Kanban 是一个**在终端启动、在浏览器中运行**的看板（Kanban）工具。每张任务卡片（Task Card）都获得独立的 **git 工作树（Worktree）**和终端（Terminal），因此可以并行运行多个编码智能体（Agent）而不会产生合并冲突。

- 这是 Cline 的**研究预览版（Research Preview）**功能
- 本地运行，无需注册账户或额外配置
- 开箱即用，支持任意 git 仓库

### 1.2 核心能力

| 能力 | 说明 |
|------|------|
| **并行执行**（Parallel Execution） | 每个任务在独立的 git worktree 和终端中运行，多个 Agent 同时工作互不干扰 |
| **统一看板**（Unified Task Board） | 在单个浏览器看板中创建、排期、关联、监控所有 Agent 任务 |
| **兼容现有 Agent**（Works With Existing Agents） | 支持 Cline CLI、Claude Code、Codex 等 CLI 编码 Agent |

### 1.3 工作原理

```
1. 运行 cline 命令 → 本地 Web 服务器在浏览器中打开看板
2. 创建任务卡片 → 可手动创建，也可让侧边栏聊天 Agent 拆分任务
3. 点击播放 → 看板创建临时工作树（Ephemeral Worktree），启动 Agent
4. 监控进度 → 每张卡片显示 Agent 的最新消息或工具调用
5. 审查差异 → 点击卡片查看所有变更，留下内联评论（Inline Comment）指导 Agent
6. 发布成果 → 点击提交（Commit）或创建拉取请求（Open PR），然后丢弃卡片清理工作树
```

---

## 2. 快速开始

### 2.1 前提条件

| 条件 | 检查命令 |
|------|---------|
| **Node.js 18 及以上** | `node --version` |
| **一个 git 仓库** | 必须在 git 仓库根目录运行 |

### 2.2 安装

全局安装 Cline CLI：

```bash
npm i -g cline
```

然后启动看板：

```bash
cline
```

> 💡 这会启动一个本地 Web 服务器并在默认浏览器中打开看板界面。

### 2.3 首次启动（Onboarding）

首次运行时会引导你完成简短设置：

1. **选择项目目录**（Project Directory）— 文件选择器打开，让你选择（或确认）要使用的工作仓库
2. **选择 Agent**（Choose Your Agent）— 选择要使用的编码 Agent（Cline、Claude Code 或 Codex）

设置完成后，你将直接进入看板，可以立即创建任务。**无需账户注册、API 密钥或配置文件。**

### 2.4 创建第一个任务

1. **创建卡片**（Create a Card）— 点击"添加"按钮创建新任务卡片
2. **编写任务描述**（Write a Task Description）— 描述你希望 Agent 完成的工作
3. **点击播放**（Hit Play）— 看板为该任务创建临时工作树（Ephemeral Worktree），并在独立的终端中启动 Agent

卡片会实时更新，显示 Agent 的最新消息或工具调用，你可以从看板直接监控进度。

> 💡 你也可以使用**侧边栏聊天**（Sidebar Chat）创建任务。打开聊天窗口，让 Agent 将工作拆分为多个任务卡片——它可以直接在看板中创建、关联并启动任务。

---

## 3. 核心工作流

### 6 步完整流程

| 步骤 | 操作 | 具体说明 |
|------|------|---------|
| **1. 创建**（Create） | 添加卡片或使用侧边栏聊天 | 任务卡片出现在看板上 |
| **2. 关联**（Link） | ⌘ + 点击连接卡片 | 建立依赖链（Dependency Chain） |
| **3. 启动**（Start） | 点击卡片上的播放按钮 | 创建临时工作树，Agent 开始工作 |
| **4. 监控**（Monitor） | 在看板上查看卡片状态 | 卡片显示 Agent 的最新消息/工具调用 |
| **5. 审查**（Review） | 点击卡片查看差异 | 完整差异对比，支持检查点和内联评论 |
| **6. 发布**（Ship） | 点击提交或创建 PR | Agent 处理合并到基础分支或创建拉取请求 |
| **7. 清理**（Clean Up） | 移入垃圾箱 | 工作树被删除，保存会话恢复 ID |

### 3.1 创建任务（Create Tasks）

两种方式：

- **手动** — 点击添加按钮，编写任务描述
- **通过侧边栏聊天**（Sidebar Chat）— 打开聊天窗口，让 Agent 将工作拆分为多个任务。Agent 可以直接在看板上创建卡片、将它们关联起来并启动工作

### 3.2 关联任务（Link Tasks）

将卡片关联起来可创建依赖链（Dependency Chain）：

- **Mac**：`⌘ + 点击` 卡片将其关联到另一张任务
- **Windows/Linux**：`Ctrl + 点击` 卡片
- 当被关联的卡片完成并移入垃圾箱时，下一张关联的卡片**自动启动**

结合自动提交（Auto-Commit）功能，可以实现**完全自动化的流水线**——一个 Agent 完成工作，输出自动传递给下一个 Agent。

### 3.3 启动任务（Start Tasks）

点击卡片上的**播放按钮**启动任务，这会发生三件事：

1. 看板为该任务创建一个**临时 git 工作树（Ephemeral Worktree）**— 仓库的隔离副本，Agent 可以在其中修改而不影响主工作目录或其他任务
2. 被 `.gitignore` 忽略的文件（如 `node_modules`）会从主仓库**符号链接（Symlink）**到工作树中，避免每个任务都重新安装依赖
3. Agent 在自己的终端中开始工作
4. 卡片显示 Agent 的**最新消息或工具调用**，你可以从看板直接监控进度

多个任务并行运行，每个在独立的工作树中，Agent 之间不会产生合并冲突。

> ⚠️ 符号链接适用于 Agent 不需要修改的 gitignored 文件（如 `node_modules`）。如果工作流要求 Agent 修改被 gitignored 的文件，请注意修改会影响符号链接目标（即主仓库中的原始文件）。

### 3.4 审查变更（Review Changes）

点击卡片打开详情视图，显示：

- **Agent 的 TUI** — 展示 Agent 对话和操作的完整文本界面
- **所有变更的差异对比**（Diff）— 工作树与基础分支之间的差异

差异查看器包含**检查点系统（Checkpoint System）**——你可以查看特定消息范围内的差异，而不仅仅是完整的累积差异。这使得理解变更内容和发生时间更加容易。

#### 内联评论（Inline Comments）

点击差异中的任意行可以留下评论。评论会被发送回 Agent 作为反馈，让你无需重写任务描述即可指导 Agent 的工作。适用于"这里换个实现方式"或"这个边界情况没处理"之类的修正。

### 3.5 发布成果（Ship It）

对变更满意后，有两个选项：

- **提交**（Commit）— 将工作树的变更合并为基础分支（Base Branch）上的一个提交
- **创建拉取请求**（Open PR）— 创建新分支并打开拉取请求

两种情况下，看板都会向 Agent 发送动态提示（Dynamic Prompt）来处理操作。Agent 将工作树转换为适当的 git 操作，并**智能处理合并冲突**——即使基础分支在工作树创建后已有新变更。

### 3.6 清理（Clean Up）

发布后，将卡片移入**垃圾箱（Trash）**以清理临时工作树并释放磁盘空间。

> 💡 如果之后需要恢复已丢弃卡片的工作，看板会为每个任务保存**会话恢复 ID（Resume ID）**，可以使用它从中断处继续。

---

## 4. 功能详解

### 4.1 临时工作树（Ephemeral Worktrees）

每张任务卡片在自己的 **git 工作树（Worktree）**中运行——这是仓库的一个隔离检出副本。这是实现并行 Agent 执行的基础：

- 每个 Agent 在自己的目录和终端中工作
- 一个工作树的变更不影响其他工作树或主工作目录
- 并行运行的 Agent 之间不会产生合并冲突
- 卡片移入垃圾箱时工作树被清理

#### 符号链接依赖（Symlinked Dependencies）

创建工作树时，看板将主仓库中被 `.gitignore` 忽略的文件（如 `node_modules`）**符号链接**到工作树中，而不是复制或重新安装。这避免了每个任务都运行 `npm install` 的开销。

> ⚠️ 符号链接指向主仓库中的原始文件。对于 Agent 不修改的依赖项来说很好用，但如果 Agent 修改了符号链接文件，变更也会影响原始文件。

### 4.2 自动提交（Auto-Commit）

启用后，Agent 在工作时会**自动将变更提交**到工作树分支。这会创建一系列增量提交（Incremental Commits），而不是在最后生成一个大差异。

可以在看板设置（Settings）中切换开启/关闭。

### 4.3 自动创建 PR（Auto-PR）

与自动提交一起启用后，Agent 在工作完成时可以**自动创建拉取请求（Pull Request）**。Agent 会使用工作树分支的变更加以生成 PR。

可以在看板设置中切换开启/关闭。

### 4.4 任务关联与依赖链（Task Linking & Dependency Chains）

任务关联可以创建顺序工作流，一个任务完成后自动触发下一个：

1. `⌘ + 点击`（Mac）或 `Ctrl + 点击`（Windows/Linux）一张卡片关联到另一张
2. 第一张卡片完成并移入垃圾箱时，被关联的卡片**自动启动**
3. 可以链式关联多张卡片实现多步骤工作流

结合自动提交功能，这可以创建**完全自动化的流水线**——一个 Agent 完成工作并提交，下一个 Agent 从中断处继续。

### 4.5 差异查看器与检查点（Diff Viewer & Checkpoints）

点击卡片打开详情视图，包含工作树完整变更的差异对比。差异查看器包含：

- **检查点作用域差异**（Checkpoint-Scoped Diffs）——可以查看特定消息范围内的变更，而不只是累积差异。有助于理解每个步骤发生了什么变更
- **内联评论**（Inline Commenting）——点击差异中的任意行留下评论，评论会被发送回 Agent。适用于需要给 Agent 针对性反馈的场景，比如"处理这个边界情况"或"用不同的模式实现"

### 4.6 侧边栏聊天与看板管理（Sidebar Chat & Board Management）

侧边栏聊天给你一个**对话式界面**来管理看板。与其手动创建和配置卡片，你可以让 Agent：

- 将工作拆分为多个任务卡片
- 将卡片关联成依赖链
- 在看板上启动任务

Agent 会根据你的指令直接操作看板。

### 4.7 脚本快捷方式（Script Shortcuts）

在看板设置中定义常用命令（如 `npm run dev` 或 `npm test`）。这些命令会以播放按钮的形式出现在任务卡片上，让你可以快速运行、测试或调试应用程序——无需切换到单独的终端。

### 4.8 Git 界面（Git Interface）

点击导航栏中的**分支名称**可打开完整的 git 界面，你可以：

- 浏览提交历史
- 切换分支
- 执行 fetch、pull、push
- 可视化 git 图谱（Git Graph）

无需离开看板或打开单独的 git 客户端即可管理仓库。

### 4.9 Agent 兼容性（Agent Compatibility）

看板兼容基于 CLI 的编码 Agent。它使用实验性功能绕过权限和运行时钩子，赋予 Agent 更多的自主权以无中断地工作。当前兼容的 Agent 包括：

- **Cline CLI**
- **Claude Code**
- **Codex**
- **OpenCode**

更多 Agent 运行时可在设置中查看。

### 4.10 任务恢复（Resume Tasks）

当卡片移入垃圾箱时，工作树被清理，但看板会保存一个**会话恢复 ID（Resume ID）**。如果需要继续已丢弃任务的工作，可以使用此 ID 从中断处继续，无需从头开始。

### 4.11 远程配置控制（Remote Config Gating）

对于团队和组织，看板访问权限可以通过 Cline 远程配置（Remote Config）进行控制。管理员可以控制组织内谁能访问看板，从而实现分阶段发布或将访问权限限制给特定团队。

---

## 5. 远程访问

默认情况下，看板绑定到 `127.0.0.1:3484`，只能从运行它的机器访问。下面的方法可以实现远程访问。

> ⚠️ 将看板暴露到 localhost 之外时，请确保你信任所有有权访问的设备或用户。看板提供对你 git 仓库和终端的完全访问权限。

### 5.1 本地网络访问（Local Network Access）

让同一 WiFi 下的其他设备（如手机、平板）访问看板：

```bash
# 方式一：CLI 参数
kanban --host 0.0.0.0

# 方式二：环境变量
KANBAN_RUNTIME_HOST=0.0.0.0 cline
```

然后从其他设备访问 `http://<你的机器IP>:3484`。

> ⚠️ 绑定到 `0.0.0.0` 会将看板暴露给整个局域网。仅在信任的网络（如家庭 WiFi）中使用。

### 5.2 Tailscale（推荐远程访问）

Tailscale 提供安全的远程访问，无需向互联网开放端口：

```bash
# 启动看板并绑定网络
KANBAN_RUNTIME_HOST=0.0.0.0 cline
```

然后在手机上访问你的 Tailscale 主机名：

```
http://你的机器名.tailxxxx.ts.net:3484
```

> 💡 Tailscale 创建加密的网状 VPN，连接经过加密，无需开放防火墙端口。这是远程访问最安全的选择。

### 5.3 Docker 部署

```dockerfile
FROM node:22
WORKDIR /app
EXPOSE 3484
CMD ["npx", "--yes", "kanban@latest", "--host", "0.0.0.0"]
```

```bash
docker build -t npx-kanban .
docker run -it -p 3484:3484 npx-kanban
```

### 5.4 SSH 隧道（SSH Tunnel）

在远程机器上：

```bash
kanban
```

在本地机器上：

```bash
ssh -L 3484:localhost:3484 user@remote-hostname
```

然后访问 `http://localhost:3484`。

### 5.5 Ngrok

```bash
# 安装 ngrok
brew install ngrok  # macOS
ngrok config add-authtoken $YOUR_AUTHTOKEN

# 启动看板
kanban

# 另一个终端创建隧道
ngrok http 3484
```

Ngrok 会生成一个公开 URL（如 `https://xxxx.ngrok-free.app`），分享该 URL 即可让其他人访问看板。

> ⚠️ Ngrok URL 在互联网上公开可访问。仅用于临时访问，使用完毕后停止隧道。

### 5.6 Cloudflare 隧道（Cloudflare Tunnel）

适用于生产级远程访问，支持自定义域名、访问控制和 HTTPS。需按照 [Cloudflare Tunnel 指南](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/) 配置。

### 5.7 远程访问方案对比

| 方法 | 安全性 | 复杂度 | 适用场景 |
|------|--------|--------|---------|
| **本地网络** | 低（仅局域网） | 简单 | 同一 WiFi 下的手机/平板 |
| **Tailscale** | 高（加密 VPN） | 简单 | 随时随地远程访问 |
| **Docker** | 中等（隔离） | 中等 | 服务器部署 |
| **SSH 隧道** | 高（加密） | 中等 | 安全的远程访问 |
| **Ngrok** | 低（公开 URL） | 简单 | 临时演示/分享 |
| **Cloudflare** | 高（自定义域名） | 复杂 | 生产级团队访问 |

> 💡 个人远程访问：**Tailscale** 是安全性和易用性最佳平衡。生产级团队访问：考虑 **Cloudflare 隧道**配合访问控制。

---

## 6. 附录

### 附录 A：键盘快捷键速查

| 快捷键 | 操作 |
|--------|------|
| **C** | 创建新任务卡片 |
| **⌘ + 点击**（Mac） | 关联卡片 |
| **Ctrl + 点击**（Windows/Linux） | 关联卡片 |

### 附录 B：工作流总结表

| 步骤 | 操作 | 执行效果 |
|------|------|---------|
| 创建（Create） | 添加卡片或使用侧边栏聊天 | 任务卡片出现在看板上 |
| 关联（Link） | ⌘ + 点击连接卡片 | 建立依赖链 |
| 启动（Start） | 点击卡片播放按钮 | 创建临时工作树，Agent 开始工作 |
| 监控（Monitor） | 查看卡片状态 | 卡片显示 Agent 最新消息/工具调用 |
| 审查（Review） | 点击卡片查看差异 | 完整差异对比 + 检查点 + 内联评论 |
| 发布（Ship） | 点击提交或创建 PR | Agent 处理合并或创建 PR |
| 清理（Clean Up） | 移入垃圾箱 | 工作树删除，保存恢复 ID |

### 附录 C：关键术语中英对照表

| 中文 | 英文 | 说明 |
|------|------|------|
| 看板 | Kanban | 可视化任务管理面板 |
| 任务卡片 | Task Card | 看板上的单个任务单元 |
| 智能体 | Agent | 执行编码任务的 AI 程序 |
| 临时工作树 | Ephemeral Worktree | git 的隔离工作目录副本 |
| 符号链接 | Symlink | 文件/目录的引用指针 |
| 依赖链 | Dependency Chain | 卡片之间的先后依赖关系 |
| 自动提交 | Auto-Commit | Agent 自动增量提交变更 |
| 拉取请求 | Pull Request / PR | 代码变更的审查请求 |
| 差异对比 | Diff | 代码变更的逐行比较 |
| 检查点 | Checkpoint | 差异可定位到特定消息范围 |
| 内联评论 | Inline Comment | 在差异行上直接添加的评论 |
| 侧边栏聊天 | Sidebar Chat | 管理看板的对话式界面 |
| 会话恢复 ID | Resume ID | 用于恢复已丢弃任务的标识符 |
| 基础分支 | Base Branch | 合并变更的目标分支 |
| 远程访问 | Remote Access | 从其他设备访问看板 |
| 研究预览版 | Research Preview | 仍在开发中的实验性功能 |

---

> 📅 编写日期：2026-05-13  
> 📌 基于 Cline Kanban 官方文档整理  
> 🔗 相关链接：[GitHub 仓库](https://github.com/cline/kanban) | [npm 包](https://www.npmjs.com/package/kanban) | [Discord #kanban](https://discord.gg/cline)