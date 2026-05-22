# PA Agent — AI K线分析辅助工具

> 面向主观交易者的 AI K线分析决策助手，基于 DeepSeek V4 Pro 大模型，帮助交易者快速识别市场结构、通道形态与交易机会。

---

## 目录

- [项目简介](#项目简介)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [启动程序](#启动程序)
- [运行测试](#运行测试)
- [目录结构](#目录结构)
- [配置文件](#配置文件)
- [常见问题](#常见问题)

---

## 项目简介

PA Agent 是一款专为主观交易者设计的 AI 辅助分析工具。它通过截图上传 K 线图，调用 DeepSeek 大模型进行市场结构分析，识别通道、震荡区间、极速行情等形态，并给出交易建议。

主要功能：

- 📊 K线图截图上传与 AI 分析
- 🔍 市场结构自动识别（通道、震荡区间、极速行情等）
- 💡 基于历史经验库的交易建议
- 📝 交易记录管理与复盘
- 🔒 API Key 本地加密存储

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 11 |
| Python | 3.11（推荐使用官方安装包） |
| 显卡 | 无特殊要求 |
| 网络 | 需要访问 DeepSeek API |

---

## 安装步骤

### 1. 安装 Python 3.11

从 [python.org](https://www.python.org/downloads/release/python-3110/) 下载 Python 3.11 安装包。

安装时勾选 **"Add Python to PATH"**。

验证安装：

```cmd
python --version
```

### 2. 克隆或下载项目

```cmd
git clone <仓库地址>
cd PA_Agent
```

### 3. 创建虚拟环境（推荐）

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 4. 安装依赖

```cmd
pip install -e ".[dev]"
```

> 如果安装速度较慢，可使用国内镜像：
> ```cmd
> pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 5. 配置 API Key

首次启动后，在程序设置界面输入 DeepSeek API Key，程序会自动加密保存到本地。

---

## 启动程序

```cmd
python -m pa_agent.main
```

或使用安装后的命令行入口：

```cmd
pa-agent
```

---

## 运行测试

运行全部测试：

```cmd
pytest
```

跳过端到端测试（不需要 GUI 环境）：

```cmd
pytest -m "not e2e"
```

仅运行单元测试：

```cmd
pytest -m unit
```

仅运行属性测试：

```cmd
pytest -m property
```

查看详细输出：

```cmd
pytest -v
```

---

## 目录结构

```
PA_Agent/
├── pa_agent/                  # 主程序包
│   ├── main.py                # 程序入口
│   ├── app_context.py         # 全局应用上下文
│   ├── ai/                    # AI 调用模块（DeepSeek API）
│   ├── config/                # 配置加载与管理
│   ├── data/                  # 数据获取（TradingView 等）
│   ├── gui/                   # PyQt6 图形界面
│   ├── indicators/            # 技术指标计算
│   ├── orchestrator/          # 分析流程编排
│   ├── records/               # 交易记录管理
│   ├── security/              # API Key 加密存储
│   └── util/                  # 通用工具函数
├── tests/                     # 测试套件
│   ├── unit/                  # 单元测试
│   ├── property/              # 属性测试（Hypothesis）
│   ├── integration/           # 集成测试
│   └── e2e/                   # 端到端测试
├── config/                    # 运行时配置文件（本地，不提交 Git）
├── experience/                # 历史经验库（成功/失败案例）
├── logs/                      # 运行日志
├── records/                   # 交易记录
├── prompt_engineering/        # 提示词文件
├── pyproject.toml             # 项目配置与依赖
└── README.md                  # 本文件
```

---

## 配置文件

配置文件位于 `config/` 目录下，首次运行时自动生成，**不会**提交到 Git。

| 文件 | 说明 |
|------|------|
| `config/settings.json` | 本机主配置（API Key 经 DPAPI 加密为 `api_key_encrypted`） |
| `config/settings.example.json` | 可提交到仓库的模板，不含真实密钥 |
| `config/exception_state.json` | 异常状态记录，用于程序崩溃后的状态恢复 |

### 防止密钥被 `git push` 到 GitHub

1. 克隆或拉取后执行一次（仅需本机）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\setup_git_secrets.ps1
   ```
   会启用 `.githooks/pre-commit`，在提交前拦截 `settings.json`、日志、分析记录等。
2. 在 GUI「设置」里填写 API Key，或复制 `config/settings.example.json` 为 `config/settings.json` 后再配置；**不要**把真实 Key 写进会被提交的文档或测试文件。
3. 默认 `pytest` **不会**跑需真实网络的 `live` 测试；仅在你显式设置环境变量时运行，例如：
   ```cmd
   set KKAI_API_KEY=sk-...
   pytest -m live -v
   ```

> ⚠️ 请勿手动编辑 `settings.json`，除非你了解各字段含义。配置损坏时可删除该文件，程序将重新生成默认配置。

---

## 常见问题

### Q: 启动时提示 `ModuleNotFoundError: No module named 'pa_agent'`

确保已在项目根目录（`PA_Agent/`）下执行安装命令，并激活了虚拟环境：

```cmd
.venv\Scripts\activate
pip install -e ".[dev]"
```

---

### Q: 启动时提示 `No module named 'PyQt6'`

PyQt6 未正确安装。重新执行：

```cmd
pip install PyQt6
```

---

### Q: 提示 `DLL load failed` 或 PyQt6 相关 DLL 错误

通常是 Visual C++ 运行库缺失。下载并安装 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)。

---

### Q: API 调用失败，提示网络错误

1. 检查网络连接是否正常
2. 确认 DeepSeek API Key 已正确配置
3. 如使用代理，确保代理设置正确

---

### Q: 测试运行时提示 `cannot connect to X server` 或 GUI 相关错误

使用 `-m "not e2e"` 跳过需要 GUI 的端到端测试：

```cmd
pytest -m "not e2e"
```

---

### Q: `config/settings.json` 损坏导致程序无法启动

删除配置文件，程序启动时会自动重新生成默认配置：

```cmd
del config\settings.json
```

---

### Q: 如何更新程序

```cmd
git pull
pip install -e ".[dev]"
```

---

### Q: 日志文件在哪里

运行日志保存在 `logs/` 目录下，可用文本编辑器查看。
