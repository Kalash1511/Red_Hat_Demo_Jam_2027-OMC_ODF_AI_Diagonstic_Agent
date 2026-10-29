# OMC ODF Agent

**OMC ODF Agent** (`omc-odf-agent`) is an AI-powered, agentic diagnostic and troubleshooting tool for Ceph and OpenShift Data Foundation (ODF) clusters. 

Built on top of [LangGraph](https://python.langchain.com/docs/langgraph) and [LangChain](https://python.langchain.com/), this project utilizes Large Language Models (LLMs) to interactively monitor cluster health, diagnose OSD/storage pool issues, and chat with operators via a responsive [Streamlit](https://streamlit.io/) web interface.

## Features

* **Intelligent Agents (LangGraph):** Features specialized AI agents for different operational domains:
  * `ceph_health`: Diagnoses overall Ceph cluster health and metrics.
  * `odf_chat_agent`: General-purpose assistant for ODF cluster queries.
  * `odf_troubleshooting_agent`: Deep-dive troubleshooting and routing for complex cluster issues.
* **Multi-LLM Support:** Built-in integrations for multiple AI models via `langchain`, including **Google Gemini**, **Groq**, and **OpenAI/MaaS** providers.
* **Live Cluster Interaction:** Executes and parses real Ceph commands (`ceph health`, `ceph osd`, `crush`, `pool`) to fetch live state and generate accurate assessments.
* **Interactive UI:** A multi-page Streamlit application offering:
  1. Ceph Health Dashboard
  2. Cluster Chat
  3. Troubleshooting Chat
* **Tool Calling & Routing:** Uses dynamic tool registries to allow the AI to selectively call OpenShift/Ceph operator commands based on user queries.

## 📂 Project Structure

```text
src/
├── agent/            # LangGraph agent definitions, nodes, and state graphs
├── ceph/             # Ceph command execution, aggregation, and parsing logic
├── llm/              # LLM provider integrations (Gemini, Groq, MaaS)
├── omc_client/       # OMC (OpenShift Managed Cluster) API client wrappers
├── operator_commands/# Operator-specific command definitions
├── state/            # State schemas for LangGraph workflows 
├── streamlit_ui/     # Streamlit frontend (Pages, Components, Services)
└── tools/            # LangChain tools and tool registries for agent access
```

## Prerequisites

* **Python:** `>= 3.11`
* **Package Manager:** [uv](https://github.com/astral-sh/uv) (An extremely fast Python package and project manager)
* **Graphviz:** Required by `pygraphviz` to generate agent state graphs (e.g., `sudo apt-get install graphviz graphviz-dev` on Ubuntu or `brew install graphviz` on macOS).

## Installation

This project uses `uv` for dependency management. 

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd omc-odf-agent
   ```

2. **Sync and install dependencies using `uv`:**
   `uv` will automatically create a virtual environment and install the dependencies listed in your `pyproject.toml`.
   ```bash
   uv sync
   ```
   *(Alternatively, you can manually create a venv and install via `uv pip install -e .`)*

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory (or in `src/llm/.env` as structured in the project) and add your required API keys.
   ```env
   # Example .env configuration
   GEMINI_API_KEY="your_google_gemini_api_key"
   GROQ_API_KEY="your_groq_api_key"
   OPENAI_API_KEY="your_openai_api_key"
   
   # Add any specific OMC/Ceph endpoint URLs or authentication tokens here
   ```

## Usage

### Starting the Streamlit UI

To launch the web interface, use `uv run` to execute Streamlit within the project's virtual environment:

```bash
uv run streamlit run src/streamlit_ui/Home_Page.py
```

This will spin up a local server (usually at `http://localhost:8501`) where you can access the Ceph Health dashboard and Chat interfaces.

### Generating Agent Graphs

If you need to visualize the LangGraph flows (outputted as PNGs), you can run the graph generator script:
```bash
uv run python src/agent/graph_png_generator/generate_all_graphs.py
```

## 🧪 Testing

The project uses `pytest` for unit and integration testing. Test configuration is handled via `pyproject.toml`.

To run the full test suite:
```bash
uv run pytest
```

To run a specific test file (e.g., Ceph diagnostic tools):
```bash
uv run pytest src/ceph/test_ceph_diagnostic.py
```

## 📦 Dependencies

Major dependencies include:
* `google-genai` & `langchain-google-genai`
* `langchain`, `langchain-groq`, `langchain-openai`
* `langgraph` (for stateful multi-actor agent orchestration)
* `streamlit` (for the frontend UI)
* `pygraphviz` (for visualizing agent state graphs)

*For a full list of dependencies, refer to the `pyproject.toml` file.*