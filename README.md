# Teachable AI Coding Personality Lab

一个可运行的编程教育实验原型，用大五人格框架设定“可教 AI 学生”。学生负责教 AI 用 C++ 解编程题，系统记录互动日志，用于分析人格条件对解释、测试、调试和学习互动的影响。

## 功能

- 6 种智能体条件：开放性、尽责性、外向性、宜人性、神经质、无特定人格
- 10 道 C++ 编程题
- 浏览器交互界面
- 后端 API
- 调用 OpenAI-compatible 大模型接口生成智能体回复
- JSONL 实验日志
- 无第三方依赖，Python 标准库即可运行

## 配置大模型

方式一：在当前项目目录创建 `.env` 文件：

```text
OPENAI_API_KEY=你的_API_Key
OPENAI_MODEL=你的模型名
OPENAI_BASE_URL=https://api.openai.com/v1
```

如果你使用兼容 OpenAI Chat Completions 格式的其他服务，把 `OPENAI_BASE_URL` 改成对应地址即可。

方式二：在 PowerShell 里临时设置：

```powershell
$env:OPENAI_API_KEY="你的_API_Key"
$env:OPENAI_MODEL="你的模型名"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
```

## 启动

```powershell
cd C:\Users\ChengHui\Desktop\编程辅导\teachable_ai_coding
python app.py
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

如果 8000 端口被占用，可以指定端口：

```powershell
python app.py --port 8010
```

## 测试

```powershell
python tests\test_engine.py
```

## 日志

互动日志会写入：

```text
data/interactions.jsonl
```

每行是一条 JSON 记录，包含：

- participant_id
- session_id
- personality
- task_id
- turn_id
- student_message
- agent_message
- 自动编码指标，如 code_present、test_case_count、debugging_count

## 工程结构

```text
teachable_ai_coding/
  app.py
  engine.py
  experiment.py
  storage.py
  static/
    index.html
    styles.css
    app.js
  tests/
    test_engine.py
  data/
    interactions.jsonl
```
