# IT Support Agent

An AI-powered Level 1 incident responder that investigates simulated server incidents using OpenAI function calling. It checks server health and logs, restarts services under critical CPU load, and escalates complex failures to a human engineer.

## Architecture

See [docs/architecture.md](docs/architecture.md) for Mermaid diagrams covering the system overview, request flow, agent loop, tool registry, and incident decision flow.

```
User incident  -->  run_it_agent()  -->  OpenAI GPT-4o-mini
                         |                       |
                   Tool registry        Health metrics and logs
                         |                       |
              Restart or escalate  <--  Simulated server data
```

## Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- Network access to the OpenAI API

This is a learning prototype. Metrics, logs, restarts, and escalations are simulated in memory; no real infrastructure is changed.

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/SashyCashy/IT-Support-Agent.git
   cd IT-Support-Agent
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS / Linux
   .venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**

   Create a `.env` file in the project root:

   ```bash
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   ```

   The app reads this file at startup. The `.env` file is ignored by Git.

## Usage

1. **Activate the environment**

   ```bash
   source .venv/bin/activate
   ```

2. **Run the demonstration scenarios**

   ```bash
   python app.py
   ```

   The main entry point sends five hardcoded incidents to the agent:

   | Server              | Condition                         | Expected response             |
   | ------------------- | --------------------------------- | ----------------------------- |
   | `payment-server-01` | CPU at 98%, process hung          | Restart and possibly escalate |
   | `db-node-02`        | Normal metrics and logs           | Report healthy                |
   | `auth-service-03`   | Memory at 95%, out-of-memory logs | Restart or escalate           |
   | `search-index-09`   | Connection refused dependency     | Escalate                      |
   | `frontend-node-04`  | Normal metrics and 200 OK logs    | No action                     |

3. **Run one incident programmatically**

   ```python
   from app import run_it_agent

   run_it_agent("The payment-server-01 is extremely slow and timing out.")
   ```

4. **Debug in VS Code**

   Open `app.py`, add a breakpoint, press `F5`, and select **Debug IT support agent**. The included debugger uses `.venv/bin/python`.

   Useful breakpoints include:
   - `while True`: each model round
   - `response_msg`: inspect the OpenAI response
   - `tool_call.function.name`: inspect the selected tool
   - `tool_output`: inspect the tool result

   Inspect these expressions in the Debug Console:

   ```python
   response_msg.tool_calls
   func_name
   func_args
   tool_output
   messages
   ```

## Project Structure

```
IT-Support-Agent/
├── app.py                  # Main agent, tools, schemas, and CLI runner
├── requirements.txt        # Python dependencies
├── .env                    # OpenAI API key, not committed
├── .vscode/
│   └── launch.json         # VS Code debugger configuration
└── docs/
    └── architecture.md    # Mermaid architecture diagrams
```

## Configuration

| Setting            | Location | Description                                |
| ------------------ | -------- | ------------------------------------------ |
| `OPENAI_API_KEY`   | `.env`   | API key used by the OpenAI client          |
| Model              | `app.py` | `gpt-4o-mini`                              |
| Tool choice        | `app.py` | `auto`, allowing the model to select tools |
| Python environment | `.venv/` | Project-local virtual environment          |

### Agent Workflow

The agent follows this general workflow:

1. Check server CPU, memory, and status.
2. Fetch recent logs.
3. Restart when CPU is greater than 90%.
4. Escalate when logs contain `ERROR` or `CRITICAL` conditions that require human investigation.
5. Return a final incident summary.

The `AVAILABLE_FUNCTIONS` registry maps model-selected tool names to Python functions. Each tool returns a JSON string that is appended to the conversation before the next model turn.

## Dependencies

| Package         | Purpose                                                  |
| --------------- | -------------------------------------------------------- |
| `openai`        | OpenAI chat completions and tool calling                 |
| `python-dotenv` | Load `OPENAI_API_KEY` from `.env`                        |
| `streamlit`     | Declared dependency for possible future UI work          |
| `pandas`        | Declared dependency for possible future data handling    |
| `tabulate`      | Declared dependency for possible future formatted output |

## Limitations

- Server metrics and logs are hardcoded for five simulated servers.
- Restart and escalation actions do not affect real services or create persistent tickets.
- The current restart guardrail checks CPU; the intended policy also includes memory above 90%.
- API, proxy, or certificate problems must be resolved in the local Python environment.
- The agent loop has limited handling for API failures, malformed arguments, and unknown tool names.

## License

This is a personal project for learning and experimentation.
