# Batch 3 · 08_deploy — 讨论原始记录
> 生成时间: 2026-05-14T07:01:36.985345
> 模型: primary=gemini-2.5-flash, critic=gpt-4.1-mini, convergence=deepseek-v4-flash
---
## Phase 1: 发散 — 各角色回答
### critic
1. **严重性**：High  
   **具体说明**：方案中使用了 conda 环境管理，但在 Windows 上，conda 的路径配置常导致环境激活失败，尤其是在命令行或脚本中调用时。若未明确说明 Windows 用户如何正确配置 conda，可能导致部署失败。  
   **修改建议**：补充 Windows 平台下 conda 环境激活的详细说明，推荐使用 `conda init` 并在脚本中使用 `conda activate` 的标准写法，或者提供基于 PowerShell/cmd 的示例。

2. **严重性**：High  
   **具体说明**：方案未明确说明 `.env` 文件的 Git 忽略策略，存在 `.env` 文件被提交到代码仓库的风险，暴露 API Key 等敏感信息，尤其在公开仓库中极具安全隐患。  
   **修改建议**：在文档中明确要求将 `.env` 文件加入 `.gitignore`，并提供示范 `.env.example` 文件供用户参考。演示环境中应使用环境变量管理工具或安全存储服务保护 API Key。

3. **严重性**：Medium  
   **具体说明**：方案中使用的 `sentence-transformers` 库在 Windows 平台上对 CUDA 支持有限，且模型下载（约100MB）和 FAISS 索引构建耗时较长，用户首次启动体验较差，未提供进度提示或缓存机制。  
   **修改建议**：建议文档中加入首次启动的时间预估和进度提示说明，提供模型缓存路径配置，或者允许用户提前手动下载模型以加快启动速度。

4. **严重性**：Medium  
   **具体说明**：方案中使用 Makefile 来管理部署命令，但 Makefile 在 Windows 平台默认不可用，且未提供等效的 PowerShell 或 cmd 脚本替代方案，导致 Windows 用户无法顺利执行自动化步骤。  
   **修改建议**：提供针对 Windows 的批处理脚本或 PowerShell 脚本版本，或者推荐使用跨平台的任务运行工具（如 npm scripts、Invoke等）替代 Makefile。

5. **严重性**：Low  
   **具体说明**：方案未包含首次启动的检查清单及常见问题排查指南，用户遇到问题时缺乏快速定位和解决方案，影响体验。  
   **修改建议**：补充一份“首次启动检查清单”，涵盖环境依赖、网络连接、模型下载状态等，并添加常见错误及解决方法章节，提升文档完整性和用户友好度。

### primary
好的，作为一名 DevOps 工程师，我将为您的 Clinical Reasoning Agent — MCRM 项目设计一套 MVP 演示阶段的部署方案。目标是在保证项目可维护性的前提下，实现快速、便捷的演示部署。

---

## 1. 本地开发环境

### `conda environment.yml` 完善建议

除了您提到的核心技术栈，为了开发、测试和代码质量，建议添加以下依赖：

*   **核心库**: `numpy`, `pandas` (数据处理常用), `scikit-learn` (FAISS 依赖或相关工具), `tqdm` (进度条)。
*   **开发/测试工具**: `pytest`, `pytest-cov` (测试覆盖率), `black` (代码格式化), `isort` (导入排序), `mypy` (类型检查), `flake8` (代码风格检查), `pre-commit` (Git Hooks 管理), `python-dotenv` (`.env` 文件加载)。

```yaml
name: mcrm
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - sqlite
  - networkx
  - faiss-cpu  # 或者 faiss-gpu 如果有GPU需求
  - numpy
  - pandas
  - scikit-learn
  - tqdm
  # 开发/测试工具 (可以通过 pip 安装，但 conda 安装更统一)
  - pytest
  - pytest-cov
  - black
  - isort
  - mypy
  - flake8
  - pre-commit
  - python-dotenv
  - pip:
    - streamlit
    - sentence-transformers
    # 其他通过 pip 安装的特定版本库
    # - some-other-lib==1.2.3
```

### `requirements.txt`

对于 MVP 演示阶段，为了确保环境的稳定性和可复现性，建议锁定版本。同时，为了区分运行时依赖和开发时依赖，可以创建两个文件：

*   `requirements.txt`: 运行时依赖 (用于演示部署和 Streamlit Cloud)。
*   `requirements-dev.txt`: 开发时依赖 (包含测试、linting 工具)。

**`requirements.txt` (锁定版本)**

```
streamlit==1.30.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
networkx==3.2.1
numpy==1.26.2
pandas==2.1.4
scikit-learn==1.3.2
tqdm==4.66.1
python-dotenv==1.0.0
# 其他核心运行时依赖...
```
*建议使用 `pip freeze > requirements.txt` 在一个干净的 conda 环境中生成此文件。*

**`requirements-dev.txt` (开发时依赖)**

```
-r requirements.txt
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.1
isort==5.12.0
mypy==1.7.1
flake8==6.1.0
pre-commit==3.6.0
# 其他开发工具...
```

### `.env` 模板设计

使用 `python-dotenv` 库来管理环境变量。创建一个 `.env.example` 文件作为模板。

```ini
# .env.example

# --- 核心项目配置 ---
# 应用程序运行模式：'development', 'production', 'testing'
APP_ENV=development

# 数据文件目录，用于存放FAISS索引、SQLite数据库等
# 默认值：./data
DATA_DIR=./data

# 嵌入式模型文件目录，用于存放sentence-transformers模型
# 默认值：./models
MODEL_DIR=./models

# SQLite数据库文件路径
# 默认值：${DATA_DIR}/mcrm.db
SQLITE_DB_PATH=${DATA_DIR}/mcrm.db

# Streamlit服务器端口
# 默认值：8501
STREAMLIT_SERVER_PORT=8501

# --- 日志配置 ---
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
# 默认值：INFO
LOG_LEVEL=INFO

# --- 调试配置 ---
# 是否开启调试模式，影响Streamlit界面是否展示调试信息
# 默认值：False
DEBUG_MODE=False

# --- 外部API密钥 (如果未来有的话) ---
# OPENAI_API_KEY=your_openai_api_key_here
```

**变量说明**:

*   **必须设置**: 对于 MVP 阶段，如果 `DATA_DIR` 和 `MODEL_DIR` 不在项目根目录，则需要明确设置。`SQLITE_DB_PATH` 可以基于 `DATA_DIR` 自动生成。
*   **有默认值**: `APP_ENV`, `STREAMLIT_SERVER_PORT`, `LOG_LEVEL`, `DEBUG_MODE` 可以有合理的默认值。

### `Makefile` 或 `taskfile` 简化常用命令

强烈建议使用 `Makefile` 来简化开发和部署流程中的常用命令。

```makefile
# Makefile

.PHONY: setup dev test lint type-check clean run

# 定义变量
CONDA_ENV_NAME = mcrm
PYTHON_VERSION = 3.11
STREAMLIT_APP = app.py # 假设您的Streamlit主文件是app.py

# 设置本地环境变量文件
ENV_FILE = .env

# 默认目标
all: run

# 初始化开发环境
setup:
	@echo "Setting up conda environment '$(CONDA_ENV_NAME)'..."
	conda env create -f environment.yml || conda env update -f environment.yml
	@echo "Activating environment and installing dev dependencies..."
	conda activate $(CONDA_ENV_NAME) && pip install -r requirements-dev.txt
	@echo "Installing pre-commit hooks..."
	conda activate $(CONDA_ENV_NAME) && pre-commit install
	@echo "Environment setup complete."

# 激活环境并进入交互式shell
dev:
	@echo "Activating development environment..."
	conda activate $(CONDA_ENV_NAME)
	@bash

# 运行所有测试
test:
	@echo "Running tests..."
	conda activate $(CONDA_ENV_NAME) && pytest --cov=./ --cov-report=term-missing

# 运行代码格式化检查 (black, isort)
lint:
	@echo "Running code linting (black, isort, flake8)..."
	conda activate $(CONDA_ENV_NAME) && black --check .
	conda activate $(CONDA_ENV_NAME) && isort --check-only .
	conda activate $(CONDA_ENV_NAME) && flake8 .

# 运行类型检查 (mypy)
type-check:
	@echo "Running type checking (mypy)..."
	conda activate $(CONDA_ENV_NAME) && mypy .

# 清理生成的Python文件和缓存
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .coverage .ipynb_checkpoints
	@echo "Cleanup complete."

# 启动Streamlit应用
run:
	@echo "Starting Streamlit application..."
	conda activate $(CONDA_ENV_NAME) && streamlit run $(STREAMLIT_APP) --server.port $(shell grep STREAMLIT_SERVER_PORT $(ENV_FILE) | cut -d'=' -f2 || echo 8501)
```

---

## 2. 演示部署方案

### 最简方案: Streamlit Cloud + 固定假数据

*   **适用场景**: 快速验证 UI/UX，无需复杂数据加载或本地文件访问。
*   **配置**:
    1.  确保您的 Streamlit 应用 (`app.py` 或其他) 在 GitHub 仓库的根目录。
    2.  `requirements.txt` 必须在仓库根目录，且只包含运行时依赖。
    3.  **数据**: 将少量固定假数据直接硬编码到 `app.py` 中，或作为小型 CSV/JSON 文件随代码一同上传。**不涉及 FAISS 索引或模型下载**。
    4.  访问 [Streamlit Cloud](https://share.streamlit.io/)，连接您的 GitHub 仓库，选择 `main` 分支和 `app.py` 文件进行部署。

### 本地方案: 用户自己装 conda + 下载索引文件 (推荐 MVP 演示)

这是最符合您“5分钟内跑起来”需求且能处理实际数据的方案。

*   **步骤**:
    1.  **安装 Miniconda/Anaconda**: 用户需自行安装。
    2.  **下载项目代码**: `git clone <repo_url>`。
    3.  **运行初始化脚本**: 提供一个脚本 (`setup_demo.sh` 或 `setup_demo.bat`) 来自动化环境创建、依赖安装和数据下载。

*   **初始化脚本设计 (`setup_demo.sh`)**:
    这个脚本将处理环境创建、依赖安装、数据下载和应用启动。

    ```bash
    #!/bin/bash

    # setup_demo.sh - MCRM Clinical Reasoning Agent Demo Setup Script

    # --- Configuration ---
    CONDA_ENV_NAME="mcrm"
    PYTHON_VERSION="3.11"
    STREAMLIT_APP="app.py" # 您的Streamlit主文件
    DEMO_DATA_URL="https://example.com/path/to/mcrm_demo_data.zip" # 替换为您的实际数据下载链接
    DEMO_DATA_ARCHIVE="mcrm_demo_data.zip"
    DATA_DIR="./data"
    MODEL_DIR="./models"
    LOG_FILE="./mcrm_setup.log"

    # --- Functions ---
    log() {
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
    }

    error_exit() {
        log "ERROR: $1"
        exit 1
    }

    # --- Main Script ---
    log "Starting MCRM Demo Setup..."
    log "Logging output to $LOG_FILE"

    # 1. Check for Conda
    if ! command -v conda &> /dev/null; then
        error_exit "Conda is not installed. Please install Miniconda or Anaconda first."
    fi
    log "Conda found."

    # 2. Create/Update Conda Environment
    log "Creating/Updating conda environment '$CONDA_ENV_NAME'..."
    conda env create -f environment.yml --name "$CONDA_ENV_NAME" || conda env update -f environment.yml --name "$CONDA_ENV_NAME"
    if [ $? -ne 0 ]; then
        error_exit "Failed to create/update conda environment."
    fi
    log "Conda environment '$CONDA_ENV_NAME' ready."

    # 3. Activate Environment and Install Python Dependencies
    log "Activating environment and installing Python dependencies..."
    source "$(conda info --base)/etc/profile.d/conda.sh" # Ensure conda commands are available
    conda activate "$CONDA_ENV_NAME"
    if [ $? -ne 0 ]; then
        error_exit "Failed to activate conda environment '$CONDA_ENV_NAME'."
    fi

    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        error_exit "Failed to install Python dependencies."
    fi
    log "Python dependencies installed."

    # 4. Download and Extract Demo Data
    mkdir -p "$DATA_DIR" "$MODEL_DIR" # Ensure data and model directories exist
    log "Downloading demo data from $DEMO_DATA_URL..."
    curl -L "$DEMO_DATA_URL" -o "$DEMO_DATA_ARCHIVE"
    if [ $? -ne 0 ]; then
        error_exit "Failed to download demo data."
    fi
    log "Demo data downloaded. Extracting to '$DATA_DIR' and '$MODEL_DIR'..."
    unzip -o "$DEMO_DATA_ARCHIVE" -d . # 解压到当前目录，假设压缩包内有 data/ 和 models/ 结构
    if [ $? -ne 0 ]; then
        error_exit "Failed to extract demo data."
    fi
    rm "$DEMO_DATA_ARCHIVE" # Clean up archive
    log "Demo data extracted and ready."

    # 5. Set up .env file (if not exists)
    if [ ! -f .env ]; then
        log "Creating .env file from .env.example..."
        cp .env.example .env
        # Optional: Modify .env with specific paths if needed, e.g.,
        # sed -i '' "s|DATA_DIR=./data|DATA_DIR=$(pwd)/data|" .env # For macOS
        # sed -i "s|DATA_DIR=./data|DATA_DIR=$(pwd)/data|" .env # For Linux
    fi

    # 6. Start Streamlit Application
    log "Starting Streamlit application..."
    # 从 .env 文件中读取端口，如果不存在则使用默认值
    STREAMLIT_PORT=$(grep STREAMLIT_SERVER_PORT .env 2>/dev/null | cut -d'=' -f2 | xargs)
    if [ -z "$STREAMLIT_PORT" ]; then
        STREAMLIT_PORT="8501"
    fi
    log "Streamlit will run on port $STREAMLIT_PORT"
    streamlit run "$STREAMLIT_APP" --server.port "$STREAMLIT_PORT" --server.headless true # --server.headless true 避免在浏览器中自动打开，方便演示者手动操作
    if [ $? -ne 0 ]; then
        error_exit "Failed to start Streamlit application."
    fi

    log "MCRM Demo Setup Complete. Streamlit app should be running."
    ```
    *   **Windows 用户**: 需要提供一个等效的 `setup_demo.bat` 脚本，或者指导用户在 WSL (Windows Subsystem for Linux) 中运行此 bash 脚本。考虑到 Python 跨平台性，WSL 是一个不错的选择。

### Docker 方案

*   **是否需要？如果不需要，理由是什么？**
    *   **结论**: 对于 **MVP 演示阶段**，且核心需求是“**在一台新 Windows/Mac 机器上 5 分钟内跑起来**”，**不建议** 将 Docker 作为首选方案。
    *   **理由**:
        1.  **Docker Desktop 安装耗时**: 在一台新机器上安装 Docker Desktop (Windows/Mac) 本身就需要几分钟，并且可能需要重启，这会超出 5 分钟的限制。
        2.  **镜像下载时间**: 首次拉取 Docker 镜像（特别是包含 Python 环境和大型模型的镜像）可能需要几百 MB 甚至 GB 的下载量，这会显著增加启动时间。
        3.  **学习曲线**: 演示者可能不熟悉 Docker 命令，增加了操作复杂性。
        4.  **资源占用**: Docker Desktop 在后台运行会占用一定的系统资源。

    *   **何时需要**: Docker 在生产环境、持续集成/交付 (CI/CD) 流程、多服务部署以及确保环境高度一致性方面具有巨大优势。在项目进入生产阶段或需要更复杂的部署时，Docker 将是理想选择。

---

## 3. 数据分发

### FAISS 索引文件（几百 MB）如何分发？

*   **方案**: **云存储 + 统一打包下载**。
*   **具体实施**:
    1.  将 FAISS 索引文件 (`.faiss` 或相关文件)、预训练的 `sentence-transformers` 模型（如果选择预下载）、SQLite 数据库文件 (`.db`) 以及任何其他大型静态数据文件打包成一个 `.zip` 或 `.tar.gz` 压缩包。
    2.  将此压缩包上传到一个**公共可访问的云存储服务**。
        *   **GitHub Releases**: 如果文件大小在 2GB 以下，且项目是公开的，GitHub Releases 是一个非常方便的选择。
        *   **Google Drive/Dropbox**: 简单易用，但可能需要手动生成共享链接。
        *   **AWS S3/Azure Blob Storage**: 更专业和可扩展，但配置略复杂。
    3.  在 `setup_demo.sh` 脚本中，使用 `curl -L <URL> -o <filename>` 或 `wget <URL> -O <filename>` 命令下载此压缩包，然后解压到 `DATA_DIR` 和 `MODEL_DIR`。

### 嵌入式模型（all-MiniLM-L6-v2）的首次下载策略？

*   **方案**: **预下载并打包分发**。
*   **具体实施**:
    1.  在开发环境中，首次运行 `sentence-transformers` 模型时，它会自动下载到 `~/.cache/torch/sentence_transformers/` 或 `MODEL_DIR` (如果配置了)。
    2.  将下载好的 `all-MiniLM-L6-v2` 模型文件夹（通常包含 `config.json`, `pytorch_model.bin`, `tokenizer.json` 等）复制到您的项目 `models/` 目录下。
    3.  将这个 `models/all-MiniLM-L6-v2` 文件夹包含在上述的**统一数据压缩包**中。
    4.  在代码中，确保 `sentence-transformers` 加载模型时指向本地路径：
        ```python
        from sentence_transformers import SentenceTransformer
        import os

        # 从 .env 文件加载配置
        from dotenv import load_dotenv
        load_dotenv()

        MODEL_DIR = os.getenv("MODEL_DIR", "./models")
        MODEL_NAME = "all-MiniLM-L6-v2"
        LOCAL_MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

        # 优先从本地加载，如果本地没有，sentence-transformers 会尝试下载
        # 但由于我们已经预下载并打包，这里会直接加载本地文件
        model = SentenceTransformer(LOCAL_MODEL_PATH)
        ```
    *   **优点**: 避免了演示时首次运行的下载延迟，确保了离线可用性。

### 图谱数据库的初始化（SQLite schema + 预置数据）

*   **方案**: **预填充的 SQLite `.db` 文件**。
*   **具体实施**:
    1.  在开发环境中，完成 SQLite 数据库的 schema 设计和所有预置数据的导入。
    2.  将生成的 `mcrm.db` 文件（或您配置的任何名称）放置在 `data/` 目录下。
    3.  将这个 `.db` 文件包含在上述的**统一数据压缩包**中。
    4.  在代码中，通过 `.env` 中的 `SQLITE_DB_PATH` 配置来连接数据库。

### 大型文件: Git LFS？云存储？每次启动自动下载？

*   **Git LFS**:
    *   **优点**: 版本控制大型文件，与 Git 工作流集成。
    *   **缺点**: 需要用户安装 Git LFS 客户端，对于“5分钟内跑起来”的演示目标，增加了额外步骤和潜在的复杂性。
*   **云存储 (推荐)**:
    *   **优点**: 最简单直接的分发方式，用户只需 `curl` 或 `wget`。
    *   **缺点**: 缺乏版本控制（需要手动管理不同版本的数据包），但对于 MVP 演示阶段足够。
*   **每次启动自动下载**:
    *   **优点**: 确保数据最新。
    *   **缺点**: 每次启动都需要下载，耗时且依赖网络，不符合快速演示的需求。

**综合来看，对于 MVP 演示，** `云存储 + 统一打包下载` **是最佳选择。**

---

## 4. CI/CD

### GitHub Actions 配置建议

创建一个 `.github/workflows/main.yml` 文件。

```yaml
# .github/workflows/main.yml
name: MCRM CI

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run Black (code formatter check)
        run: black --check .

      - name: Run Isort (import sorter check)
        run: isort --check-only .

      - name: Run Flake8 (code style check)
        run: flake8 .

      - name: Run MyPy (type checker)
        # 假设您的代码入口在 src/ 或项目根目录
        run: mypy .

      - name: Run Pytest (unit/integration tests)
        run: pytest --cov=./ --cov-report=xml
      
      - name: Upload coverage reports to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }} # 如果使用Codecov，需要配置此Secret
          files: ./coverage.xml
          fail_ci_if_error: true
```

### 排除项

在 `.gitignore`、`pyproject.toml` (black/isort 配置) 和 `mypy.ini` 中配置排除项。

*   **`.gitignore`**:
    ```
    # Python
    __pycache__/
    *.pyc
    .pytest_cache/
    .mypy_cache/
    .env
    .venv/
    .conda/
    mcrm_setup.log # 演示脚本日志

    # Data & Models
    data/ # 包含FAISS索引、SQLite DB等
    models/ # 包含预下载的sentence-transformers模型
    mcrm_demo_data.zip # 下载的演示数据压缩包

    # Coverage
    .coverage
    htmlcov/
    .coverage.*

    # Streamlit
    .streamlit/
    ```

*   **`pyproject.toml` (用于 Black 和 Isort)**:
    ```toml
    [tool.black]
    line-length = 88
    target-version = ['py311']
exclude = '''
/(
    \.git
  | \.venv
  | \.conda
  | \.mypy_cache
  | \.pytest_cache
  | \.streamlit
  | data
  | models
  | build
  | dist
)/
'''

    [tool.isort]
    profile = "black"
    multi_line_output = 3
    include_trailing_comma = true
    force_grid_wrap = 0
    use_parentheses = true
    ensure_newline_before_comments = true
    line_length = 88
    skip_glob = [
        "data/*",
        "models/*",
    ]
    ```

*   **`mypy.ini`**:
    ```ini
    [mypy]
    python_version = 3.11
    warn_unused_configs = True
    warn_unused_ignores = True
    ignore_missing_imports = True # 某些第三方库可能没有类型提示
    exclude = (data/|models/) # 排除data和models目录
    ```

### `pre-commit` hooks

强烈建议使用 `pre-commit` 在代码提交前自动运行格式化、排序和检查。

1.  **安装**: `pip install pre-commit` (已包含在 `requirements-dev.txt`)
2.  **配置 `.pre-commit-config.yaml`**:
    ```yaml
    # .pre-commit-config.yaml
    repos:
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.5.0
        hooks:
          - id: trailing-whitespace
          - id: end-of-file-fixer
          - id: check-yaml
          - id: check-added-large-files # 检查是否添加了过大的文件
            args: ['--maxkb=500'] # 限制最大文件大小为500KB，防止误提交大型数据文件

      - repo: https://github.com/psf/black
        rev: 23.12.1
        hooks:
          - id: black

      - repo: https://github.com/PyCQA/isort
        rev: 5.12.0
        hooks:
          - id: isort

      - repo: https://github.com/pre-commit/mirrors-mypy
        rev: v1.7.1
        hooks:
          - id: mypy
            args: [--ignore-missing-imports] # 忽略缺失的导入类型提示

      - repo: https://github.com/PyCQA/flake8
        rev: 6.1.0
        hooks:
          - id: flake8
    ```
3.  **安装 hooks**: `pre-commit install` (已包含在 `Makefile` 的 `setup` 目标中)。

### 环境变量管理

*   **CI secrets**: 如果项目未来需要任何敏感信息（如 API 密钥），应将其存储在 GitHub Secrets 中，并通过 `secrets.YOUR_SECRET_NAME` 注入到 GitHub Actions 环境变量中。
    *   例如，如果使用 Codecov，`CODECOV_TOKEN` 就是一个 Secret。
*   **`.env.test`**: 对于 MVP 阶段，如果测试需要特定的非敏感配置，可以在 CI workflow 中直接设置环境变量，或者在 `pytest` 命令前加载一个 `.env.test` 文件。
    *   例如，在 GitHub Actions 中：
        ```yaml
        - name: Run Pytest with test environment variables
          run: |
            export LOG_LEVEL=DEBUG
            export DEBUG_MODE=True
            pytest
        ```
    *   对于 MCRM 项目，目前看来不需要复杂的 `.env.test` 文件，直接在 CI 中设置 `LOG_LEVEL` 或 `DEBUG_MODE` 即可。

---

## 5. 监控与日志

### MVP 阶段需要什么级别的日志？

*   **`INFO`**: 记录应用程序的正常运行状态和关键事件。
    *   示例:
        *   `INFO: Model 'all-MiniLM-L6-v2' loaded successfully.`
        *   `INFO:

---
## Phase 2: 收敛 — final_decision
综合 critic 和 primary 专家意见，最终部署方案如下：
1. 环境管理：使用 conda 创建 mcrm 环境，提供 environment.yml（含所有依赖）和 requirements.txt（锁定版本），并分离开发依赖 requirements-dev.txt。
2. 敏感信息：使用 python-dotenv 管理 .env，将 .env 加入 .gitignore，提供 .env.example 模板。
3. 跨平台脚本：同时提供 Makefile（Linux/macOS）和 setup_demo.ps1/powershell（Windows），确保用户可直接运行。
4. 数据分发：将 FAISS 索引、SQLite 数据库和预下载的 sentence-transformers 模型打包上传至 GitHub Releases，通过自动化脚本下载并解压。
5. 首次启动：脚本中加入 tqdm 进度条，文档中说明模型缓存路径和预计时间。
6. 演示部署：MVP 阶段优先使用 Streamlit Cloud + 假数据，或本地方案（用户自行安装 conda 后运行一键脚本）。暂不引入 Docker。
7. CI/CD：GitHub Actions 配置代码检查、类型检查、测试，并通过 pre-commit 确保本地提交质量。
8. 文档：补充 Windows 平台 conda 激活指南、首次启动检查清单和常见问题排查。

### consensus
- 需要清晰的 .env 文件 Git 忽略策略和示例文件
- 部署方案需覆盖 Windows 平台，包括 conda 环境激活和脚本兼容性
- 首次启动应有进度提示或预估时间，并提供模型/数据缓存机制
- 推荐使用 conda 管理 Python 环境且分离运行时与开发时依赖
- 最简演示使用 Streamlit Cloud 固定假数据
- CI/CD 应配置 GitHub Actions，集成代码格式化、类型检查、测试
- 使用 pre-commit 钩子保证代码质量
- 文档应包含首次启动检查清单和常见问题排查

### divergences
- Makefile 跨平台兼容性: majority=使用 Makefile 管理开发命令，并为 Windows 提供等效脚本或建议使用 WSL / minority=批评 Makefile 在 Windows 默认不可用，要求直接提供 PowerShell/cmd 脚本或跨平台工具 → 采纳 minority 建议：项目根目录下同时提供 Makefile 和 setup_demo.ps1/setup_demo.bat 脚本，并在文档中说明 Wi
- conda Windows 路径问题: majority=文档中默认使用 conda activate，未专门针对 Windows 阐述 / minority=指出 conda 路径配置在 Windows 上易失败，需补充详细说明和标准写法 → 采纳 minority 建议：在文档中增加 Windows 平台 conda 环境激活指南，推荐使用 conda init 并在脚本中使用 conda acti
- 首次启动模型下载策略: majority=将 sentence-transformers 模型预打包到数据压缩包中，避免运行时下载 / minority=指出模型下载和 FAISS 构建耗时，建议提供进度提示和缓存配置 → 融合：预打包模型并确保代码加载本地路径；同时在启动脚本中添加进度提示（如 tqdm），或在文档中说明首次启动耗时。
- CUDA 支持与 Windows: majority=未专门提及 CUDA 支持问题 / minority=指出 sentence-transformers 在 Windows 上 CUDA 支持有限 → 采纳 minority 建议：在文档中说明 Windows 下建议使用 CPU 版本 faiss-cpu，并提示 CUDA 支持差异；同时确保依赖声明中 fai

### risk_notes
- 数据压缩包较大（几百 MB），下载可能受网络环境影响，建议提供镜像或断点续传支持。
- Windows 用户可能未安装 conda 或 PowerShell 执行策略限制，需在文档中提示先安装 conda 并关闭脚本执行限制。
- 预打包的模型版本若与代码依赖的 sentence-transformers 版本不匹配可能出错，需确保版本锁定。
- Streamlit Cloud 方案不涉及本地数据，可能无法充分演示核心功能，但适用于快速 UI 验证。