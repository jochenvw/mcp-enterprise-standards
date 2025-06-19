# 🖥️ PC Requirements: Set the Stage

To run and develop the MCP Enterprise Standards project locally, make sure your machine is ready:

* ✅ [**Git**](https://git-scm.com/) – used to clone the code repository and manage changes.
* 🔐 Access to [**GitHub**](http://github.com) – where the code lives. You'll need access to pull and possibly push updates.
* 🐍 [**Python (Windows Store)**](https://apps.microsoft.com/detail/9PNRBTZXMB4Z?hl=en-us&gl=NL&ocid=pdpshare) – the core programming language used for the server.
* 🧠 [**GitHub Copilot**](https://github.com/features/copilot) (licensed) – optional, but helps you write and complete code using AI.
* 🧱 [**VS Code**](https://code.visualstudio.com/) – the recommended editor for this project, with great Python and container support.
* 💡 **Optional but recommended**:

  * 🐧 [**WSL2**](https://learn.microsoft.com/en-us/windows/wsl/install) – lets you run a full Linux dev environment on Windows.
  * 🐳 [**Docker Desktop**](https://apps.microsoft.com/detail/XP8CBJ40XLBWKX?hl=en-US&gl=NL&ocid=pdpshare) – enables containerized environments.
  * 📦 [**DevContainer extension**](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) – lets you work inside a reproducible development container.

---

# 💻 Open the Project in VS Code

We're using a **VS Code workspace**, not a folder. This allows settings and configurations to be shared across the team.

### ✅ Launch like this:

```bash
code mcp-enterprise-standards.code-workspace
```

*or*

```bash
code-insiders mcp-enterprise-standards.code-workspace
```

### 🧱 If you're using a DevContainer:

* Choose **“Reopen in Container”** when prompted.

### 🐍 If not using DevContainers:

* Make sure the **Python extension** for VS Code is installed for linting, formatting, and running your code smoothly.

---

# 🧪 Set Up Your Environment Variables

We use a `.env` file to configure settings (like API endpoints or secrets) without hardcoding them.

### Do this:

```bash
copy .env.sample .env
```

Then, open `.env` and edit the values based on your local setup or credentials.

---

# 🐍 Python Environment Setup

Python projects use **virtual environments** to isolate dependencies — so you don’t break system Python or clash with other projects.

### 1. 🔍 Open a terminal:

Prefer the **Command Prompt**, not PowerShell, as it's more compatible with some Python commands.

### 2. 🏗️ Create and activate your virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 📦 Install the local project (and its dependencies):

```bash
pip install .
```

### 4. 🚀 Start the server:

```bash
python src\server.py
```

### 5. 🌐 Test it:

Visit [http://localhost:8000/mcp/](http://localhost:8000/mcp/) in your browser.
You should see the MCP server running.

---

# 🧭 Final Touch: VS Code Config

The `.vscode/mcp.json` file stores local config (e.g., where your server lives or what endpoints to hit).

### Do this:

```bash
rename .vscode\mcp.json.sample .vscode\mcp.json
```

This completes your local setup! You're now ready to develop, test, and contribute.
