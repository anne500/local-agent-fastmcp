# 🔌 Local AI Agent with FastMCP

A Windows-friendly implementation of [Darsh Shah’s freeCodeCamp tutorial](https://www.freecodecamp.org/news/build-an-mcp-server-with-fastmcp-for-local-ai-agent/), with a read-only Build Release and Integration Engineering example. The default run uses your local Ollama model and needs no API key.

```mermaid
flowchart TD
    A["LangChain agent"] <-->|Local model API| B["Ollama · Qwen 3.5"]
    A <-->|stdio or Streamable HTTP| C["FastMCP tools"]
    C -->|Read by run ID| D["Saved GitHub Actions evidence"]
    C --> F["Local Markdown notes"]
    A <-->|Optional MCP over HTTP| E["DeepWiki and Hugging Face"]
    classDef agent fill:#ede9fe,stroke:#7c3aed,color:#1f1147
    classDef local fill:#dbeafe,stroke:#2563eb,color:#102453
    classDef evidence fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef remote fill:#fef3c7,stroke:#d97706,color:#422006
    class A agent
    class B,C local
    class D,F evidence
    class E remote
```

## 🟦 Run on Windows

Clone the repository or extract the ZIP, then open PowerShell in the `local-agent-fastmcp` folder. Python 3.12 was used for the packaged checks.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
ollama list
.\.venv\Scripts\python.exe .\agent_with_mcp.py
```

Keep the Ollama app running. If `qwen3.5:4b` is absent from `ollama list`, run `ollama pull qwen3.5:4b`. The agent launches the MCP server automatically with the same Python interpreter. The direct tests need Python dependencies only.

## 🟩 Verify tool behavior

| Enter at the prompt | Check in the output |
|---|---|
| Count the words in “Cedar needs a smoke test.” | `word_count` returns 5 and the final answer agrees. |
| What time is it? | `current_time` returns a local timestamp with its UTC offset. |
| What is the capital of France? | Paris, with no tool call. |
| What do we know about CI run 21890541227? Cite the source. | `get_build_evidence` returns a failed validation job and the source URL. |
| Why did CI run 21890541227 fail? | The answer reports the observed failure and says the captured evidence cannot establish its cause. |
| What do we know about CI run 99999999999? | The tool returns `missing`, and the answer reports the evidence gap. |

Match each tool call to its result using the printed call ID. A correct final answer can still hide a skipped call or incorrect argument, so check the transcript as well.

## 🟩 Extensions

| Extension | How to try it | Verification |
|---|---|---|
| 📝 **Local Markdown note reader** | Run the default agent and ask it to read the note named `cedar`. | On Windows, Qwen handled a missing note and quoted it after the file was created. Direct tests also checked path traversal. |
| 🌐 **DeepWiki** | Run the agent with `--deepwiki` and ask about `karpathy/nanochat`. | On Windows, the full-wiki call returned data but missed the one-sentence format. The focused `ask_wiki_question` call returned a result that Qwen summarized in one sentence. |
| 🤗 **Hugging Face MCP** | Run the agent with `--huggingface` and ask it to search the public Hub for `bert-base-uncased`. | With both public servers enabled on Windows, Qwen called `hub_repo_search` with a model filter and limit of one, then returned `google-bert/bert-base-uncased`. |
| 🔌 **Streamable HTTP server** | Start the server with `--http` and connect the agent with `--http-url`. | On Windows, the agent discovered four tools at `http://127.0.0.1:8001/mcp` and quoted the note returned by `read_note`. Direct adapter checks also exercised CI evidence over HTTP. |
| 🖥️ **Remote host** | Run the HTTP server on a host you control and connect over an SSH tunnel. | [Deployment steps](#-run-on-another-machine) are available. A remote host was not provisioned for this project. |
| 🟪 **BRI evidence** | Ask for a known or unknown run ID. | The Windows agent cited the known run and reported a missing record for an unknown run. |

### 📝 Read a local note

The sample is [notes/cedar.md](notes/cedar.md). Add your own UTF-8 Markdown notes under `notes/` and use lowercase names such as `release-checklist.md`. Ask for the name without its extension. The tool reads up to 16 KiB per note. Personal notes are ignored by Git. Use the default local-only mode for private notes.

### 🌐 Connect to public MCP servers

```powershell
.\.venv\Scripts\python.exe .\agent_with_mcp.py --deepwiki --huggingface
```

Enable either flag on its own if you only need one service. DeepWiki handles public GitHub repository questions. The [Hugging Face MCP server](https://github.com/huggingface/hf-mcp-server) is used through its public repository search tool. Each enabled service receives its own tool-call arguments. If discovery fails, the agent reports the failure and continues with the tools it loaded.

### 🔌 Serve tools over HTTP

Open two PowerShell windows in the project folder. Start the server in the first:

```powershell
.\.venv\Scripts\python.exe .\mcp_server.py --http
```

Connect the agent from the second and ask it to read `cedar` or look up run `21890541227`:

```powershell
.\.venv\Scripts\python.exe .\agent_with_mcp.py --http-url http://127.0.0.1:8000/mcp
```

### 🖥️ Run on another machine

On a Linux host you control, clone this repository, install the pinned dependencies in a virtual environment, and run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python mcp_server.py --http
```

From Windows, forward the remote loopback port. Replace `user@your-server` with your SSH login and keep this PowerShell window open:

```powershell
ssh -N -L 127.0.0.1:8001:127.0.0.1:8000 user@your-server
```

Run the Windows agent with `--http-url http://127.0.0.1:8001/mcp`. Ollama runs on Windows and FastMCP reads fixtures and notes on the remote host. The server binds to loopback and SSH controls remote access. A public endpoint would require its own authentication and deployment configuration.

## ✅ Observed Windows baseline

| Check | Observed result |
|---|---|
| Direct MCP and adapter integration | 2 tests passed in 6.038 seconds on the initial version. |
| Live word count | Qwen called `word_count` and used the returned count of **5**. |
| Live known CI run | Qwen cited run `21890541227` and distinguished the failed validation job from the unavailable cause. |
| Live unknown CI run | Qwen reported that the fixture had no evidence for `99999999999`. |

The note reader, DeepWiki, Hugging Face, and loopback HTTP were also verified with live Qwen on Windows. The SSH tunnel deployment remains unverified.

## 🟪 Inspect the BRI evidence

The checked-in fixture comes from [Home Assistant BRI demo run 21890541227](https://github.com/anne500/home-assistant-bri-demo/actions/runs/21890541227). It records the run attempt, commit SHA, workflow and job conclusions, and artifact count returned by GitHub. The jobs response contained no step records. The saved metadata supports a failure finding, and establishing a cause would require further evidence.

| File | Purpose |
|---|---|
| `mcp_server.py` | Tool schemas, local note and fixture lookups, and transport selection. |
| `agent_with_mcp.py` | Local Ollama agent, optional remote discovery, and tool-call transcript. |
| `fixtures/home-assistant-run.json` | Saved GitHub Actions evidence with source URLs. |
| `tests/test_stdio.py` | Subprocess tests for discovery, lookups, note path validation, and adapter integration. |
| `requirements.txt` | Dependency versions used for verification. |
