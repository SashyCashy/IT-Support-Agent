# Architecture

## System Overview

The IT Support Agent is a command-line incident responder. A natural-language incident is sent to OpenAI GPT-4o-mini, which uses the registered tools to inspect simulated server metrics and logs, restart services when resource usage is critical, and escalate dependency failures to a human engineer.

```mermaid
graph TB
    subgraph User["User / CLI"]
        A["Incident description"] --> B["app.py main runner"]
    end

    subgraph Agent["IT Support Agent"]
        B --> C["run_it_agent()"]
        C --> D["OpenAI GPT-4o-mini"]
        C --> E["AVAILABLE_FUNCTIONS registry"]
        E --> F["get_server_health()"]
        E --> G["fetch_recent_logs()"]
        E --> H["restart_service()"]
        E --> I["escalate_to_engineer()"]
    end

    subgraph Data["Simulated Data Layer"]
        J["Server metrics\nCPU, memory, status"]
        K["Server logs\n5 servers x 5 entries"]
    end

    subgraph Config["Configuration"]
        L[".env\nOPENAI_API_KEY"]
        M["requirements.txt"]
    end

    F --> J
    G --> K
    H --> F
    I --> G
    L --> C
    D <-->|"tool calls and results"| C
```

## Request Flow

```mermaid
sequenceDiagram
    actor User
    participant CLI as app.py main
    participant Agent as run_it_agent()
    participant LLM as OpenAI GPT-4o-mini
    participant Registry as AVAILABLE_FUNCTIONS
    participant Tools as Tool functions
    participant Data as Simulated metrics/logs

    User->>CLI: Start app and provide incident
    CLI->>Agent: run_it_agent(incident)
    Agent->>Agent: Build system and user messages

    loop Until no tool_calls remain
        Agent->>LLM: Send messages and tools_schema
        LLM-->>Agent: Assistant response

        alt Response contains tool calls
            loop For each requested tool
                Agent->>Registry: Resolve function name
                Registry-->>Agent: Function reference
                Agent->>Tools: Execute function(**arguments)
                Tools->>Data: Read metrics or logs
                Data-->>Tools: Return simulated data
                Tools-->>Agent: Return JSON string
                Agent->>Agent: Append assistant and tool messages
            end
        else Response is final text
            Agent-->>CLI: Print final incident summary
            CLI-->>User: Display result
        end
    end
```

## Incident Decision Flow

```mermaid
flowchart TD
    A["Incident reported"] --> B["get_server_health()"]
    B --> C{"Server found?"}
    C -- No --> D["Return unknown-server error"]
    C -- Yes --> E["fetch_recent_logs()"]
    E --> F{"CPU > 90%\nor memory > 90%?"}
    F -- Yes --> G["restart_service()"]
    F -- No --> H{"Logs show ERROR or CRITICAL?"}
    H -- Yes --> I["escalate_to_engineer()"]
    H -- No --> J["Report healthy / no action"]
    G --> K{"Dependency failure remains?"}
    K -- Yes --> I
    K -- No --> L["Report restart result"]
    I --> M["Report escalation and logs"]
```

The model orchestrates the order of tool calls, while the tool functions enforce local guardrails. `restart_service()` restarts only when CPU or memory is greater than 90%. `escalate_to_engineer()` identifies `ERROR` and `CRITICAL` log entries and returns an escalation result when any are present.

## Agent Loop

The conversation history is accumulated across model turns:

| Turn  | Role                 | Content                            |
| ----- | -------------------- | ---------------------------------- |
| 0     | `system`             | Level 1 responder instructions     |
| 1     | `user`               | Natural-language incident          |
| 2     | `assistant`          | Tool call request                  |
| 3     | `tool`               | JSON health or log result          |
| 4+    | `assistant` / `tool` | Additional investigation or action |
| Final | `assistant`          | Human-readable incident summary    |

```mermaid
stateDiagram-v2
    [*] --> SendRequest
    SendRequest --> ReceiveResponse
    ReceiveResponse --> DispatchTools: tool_calls present
    DispatchTools --> AppendResults
    AppendResults --> SendRequest
    ReceiveResponse --> PrintSummary: no tool_calls
    PrintSummary --> [*]
```

## Tool Registry

`tools_schema` describes the functions to the OpenAI API. `AVAILABLE_FUNCTIONS` performs the runtime dispatch from the model-selected function name to the Python callable.

```mermaid
flowchart LR
    A["LLM tool_calls[]"] --> B["Read function.name"]
    B --> C["Parse function.arguments"]
    C --> D{"AVAILABLE_FUNCTIONS.get(name)"}
    D -- Found --> E["Execute callable"]
    E --> F["JSON tool output"]
    F --> G["Append role=tool message"]
    G --> H["Next LLM turn"]
    D -- Missing --> I["Unknown tool handling"]
```

| Tool                   | Responsibility                         | Data source        |
| ---------------------- | -------------------------------------- | ------------------ |
| `get_server_health`    | Return CPU, memory, and status         | Metrics dictionary |
| `fetch_recent_logs`    | Return the latest log entries          | Log dictionary     |
| `restart_service`      | Restart when CPU or memory exceeds 90% | Health result      |
| `escalate_to_engineer` | Escalate ERROR or CRITICAL logs        | Log result         |

## Server Scenarios

| Server              | Metrics             | Logs                                | Expected action                  |
| ------------------- | ------------------- | ----------------------------------- | -------------------------------- |
| `payment-server-01` | CPU 98%, memory 40% | Hung process, timeout               | Restart, possibly escalate       |
| `db-node-02`        | CPU 12%, memory 60% | Normal INFO entries                 | No action                        |
| `auth-service-03`   | CPU 45%, memory 95% | OutOfMemoryError, memory leak       | Restart and investigate/escalate |
| `search-index-09`   | CPU 10%, memory 15% | Connection refused, dependency down | Escalate                         |
| `frontend-node-04`  | CPU 25%, memory 30% | Successful 200 responses            | No action                        |

The `__main__` block runs these five scenarios sequentially for demonstration and debugging.

## Dependencies and Configuration

```mermaid
graph LR
    A[".env"] --> B["python-dotenv"]
    B --> C["OPENAI_API_KEY"]
    C --> D["OpenAI client"]
    E["requirements.txt"] --> D
    E --> F["openai"]
    G[".venv"] --> D
    G --> F
```

- **Runtime:** Python 3.10+
- **LLM:** `gpt-4o-mini`
- **Configuration:** `OPENAI_API_KEY` in `.env`
- **Environment:** `.venv`
- **Entry point:** `python app.py`
- **Debugging:** `.vscode/launch.json` uses the project virtual environment

## Scope

This is a demonstration prototype. Metrics and logs are hardcoded in memory, restarts are simulated, escalation creates no persistent ticket, and there is no live monitoring API or database.
