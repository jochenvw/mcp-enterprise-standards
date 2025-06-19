# 🧠 MCP Server for Enterprise Standards

This project runs an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/introduction) server designed for **enterprise code validation**. It integrates with editors like **VS Code** and **Cursor** to provide tailored feedback inside your IDE — based on your **organization's specific standards**.

---

## 💼 Why Use This?

As an enterprise developer, you often wonder:

- Am I complying with internal policies?
- Can I expose this API endpoint?
- Is this deployment pattern secure or recommended?

GitHub Copilot can help, but **doesn’t understand your enterprise context**. With an MCP server like this one, you can supercharge Copilot with custom logic and internal rules.

🔗 [MCP servers in GitHub Copilot](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

---

## ⚙️ How It Works

1. Your org (or you locally) run this MCP server via `server.py`
2. A developer writes code (e.g. Bicep or Python) in VS Code
3. The editor is configured to use this MCP server
4. GitHub Copilot (in **Agent Mode**) calls the MCP tool
5. The server checks code against enterprise rules using an LLM endpoint
6. Copilot receives feedback and proposes refactors or improvements

---

### 🖼️ Visual Overview

![Screenshot](assets/mcp_tool.jpg)

```mermaid
graph TD
    A["Developer writing code"] -->|"Asks for feedback"| B["GitHub Copilot"]
    B -->|"Calls"| C["MCP Server"]
    C -->|"Analyzes code against"| D["Enterprise Standards"]
    C -->|"Uses"| E["LLM Endpoint"]
    E -->|"Returns analysis"| C
    C -->|"Returns feedback"| B
    B -->|"Suggests improvements"| A 
````

---

## 🚀 Getting Started

🛠️ All setup instructions have moved to [**`setup.md` →**](./setup.md)

That file includes:

* ✅ System requirements (Python, Git, VS Code, DevContainer, etc.)
* 🐍 Native (non-container) setup using `venv` and `pip`
* 🐳 Containerized setup using WSL2 + Docker + DevContainer
* 🔐 `.env` file setup and configuration
* ▶️ Commands to launch and verify the server

---

## 🔌 LLM Configuration (Required)

The server uses [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/) to connect to a Large Language Model.

You'll need a `.env` file like this:

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-32k_for_example
AZURE_OPENAI_API_VERSION=2024-05-01-preview_for_example
```

Create this by copying the sample:

```bash
cp .env.sample .env
```

Then fill in the values for your Azure OpenAI instance.

---

## 🧪 Testing Locally

After setup:

```bash
python src/server.py
```

Then open: [http://localhost:8000/mcp/](http://localhost:8000/mcp/)
You should see the MCP server interface and be ready to integrate with GitHub Copilot.

---

## 📎 Related Links

* [Model Context Protocol Overview](https://modelcontextprotocol.io/introduction)
* [GitHub Copilot MCP Server Docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
* [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
