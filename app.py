import os
import json
from pathlib import Path
from dotenv import dotenv_values
from openai import OpenAI

# 1. Read the API key exclusively from this project's .env file
dotenv_path = Path(__file__).with_name(".env")

env_key = dotenv_values(dotenv_path).get("OPENAI_API_KEY", "")

if not env_key:
    raise RuntimeError(f"OPENAI_API_KEY is missing from {dotenv_path}")

client = OpenAI(api_key=env_key)

def get_server_health(server_id: str) -> str:
    """Returns CPU and Memory usage for a given server."""

    print(f"-> Tool: Checking health for {server_id}...")

    metrics = {
        # Scenario 1: High CPU (Needs Restart)
        "payment-server-01" : { "cpu" : "98%", "memory" : "40%", "status" : "Warning" },

        # Scenario 2: Healthy (No Action Needed)
        "db-node-02": {"cpu": "12%", "memory": "60%", "status": "Healthy"},

        # Scenario 3: High Memory Leak (Needs Restart or Escalation)
        "auth-service-03": {"cpu": "45%", "memory": "95%", "status": "Critical"},

        # Scenario 4: Network/Dependency Failure (Needs Escalation)
        "search-index-09": {"cpu": "10%", "memory": "15%", "status": "Error"},

        # Scenario 5: Completely Normal
        "frontend-node-04": {"cpu": "25%", "memory": "30%", "status": "Healthy"},
    }

    result = metrics.get(server_id, { "error": f"Log not found for the {server_id}. Check the ID."})
    return json.dumps({"metrics" : result})

def fetch_recent_logs(server_id: str, lines: int = 5) -> str:
    """Return the last N lines of logs"""

    print(f" -> TOOL: Fetching last {lines} log lines for {server_id}....")

    log_database = {
        "payment-server-01" : [
            "[INFO] Request received /pay/v1",
            "[WARN] CPU threshold exceeded 90%",
            "[WARN] Thread pool exhaustion",
            "[CRITICAL] Process hung, not accepting new connections",
            "[ERROR] Timeout waiting for thread"
        ],
        "db-node-02": [
            "[INFO] Backup started",
            "[INFO] Backup completed successfully",
            "[INFO] User query executed in 12ms",
            "[INFO] Health check: OK",
            "[INFO] Replication sync active"
        ],
        "auth-service-03": [
            "[INFO] Token validated user_882",
            "[WARN] Garbage collection taking too long (>5s)",
            "[ERROR] java.lang.OutOfMemoryError: Java heap space",
            "[CRITICAL] Application crashing due to memory leak",
            "[INFO] Restarting context..."
        ],
        "search-index-09": [
            "[INFO] Indexing started",
            "[ERROR] Connection refused: elastic-cluster-main:9200",
            "[ERROR] Failed to write document ID 4432",
            "[CRITICAL] Dependency Unreachable: Search Engine is down",
            "[ERROR] Retrying in 30s..."
        ],
        "frontend-node-04": [
            "[INFO] GET /home 200 OK",
            "[INFO] GET /assets/logo.png 200 OK",
            "[INFO] GET /login 200 OK",
            "[INFO] GET /api/v1/status 200 OK",
            "[INFO] Health check passed"
        ]
    }

    logs = log_database.get(server_id, {"error":  f"Log not found for the {server_id}. Check the ID."})
    return json.dumps({"logs" : logs[:lines]});

def restart_service(server_id: str) -> str:
   """Return a JSON string confirming the restart was successful."""

   print(f"-> Tool: Restarting service...")
   response = json.loads(get_server_health(server_id))
   server_metric = response["metrics"]

   if "error" in server_metric:
    return json.dumps({"status": "error", "message": server_metric["error"]})

   percentage = float(server_metric["cpu"].strip("%"))

   if(percentage >= 90):

    return json.dumps({
       "status": "success",
       "message": f"Server {server_id} restarted successfully"
    })

   return json.dumps({
      "status": "skipped",
      "message": f"Restart not required for server {server_id}"
    })

def escalate_to_engineer(server_id: str) -> str:
   """Return a JSON string confirming the ticket was created."""

   print(f"-> Tool: Escalating to human...")

   response = json.loads(fetch_recent_logs(server_id))
   server_logs = response["logs"]

   if "error" in server_logs:
      return json.dumps({ "status": "error", "message" : server_logs["error"] })

   problem_logs = []
   for log in server_logs:
      if "ERROR" in log or "CRITICAL" in log:
         problem_logs.append(log)

   if problem_logs:
      return json.dumps({
            "status" : "escalate",
            "message": "Major issue has been detected escalating to human",
            "logs": server_logs
        })

# Registry pattern
AVAILABLE_FUNCTIONS = {
   "get_server_health": get_server_health,
   "fetch_recent_logs": fetch_recent_logs,
   "restart_service": restart_service,
   "escalate_to_engineer": escalate_to_engineer
}


tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_server_health",
            "description": "Checks the current CPU and memory usage of a specific server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server, e.g., 'payment-server-01'"}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_recent_logs",
            "description": "Retrieves the most recent log entries from a server to diagnose errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server."},
                    "lines": {"type": "integer", "description": "Number of log lines to fetch."}
                },
                "required": ["server_id"]
            }
        }
    },
    # --- >>>> TASK 3: Define Schema for restart_service ---
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "### TODO: Write a description for the AI",
            "parameters": {
                "type": "object",
                "properties": {
                   "server_id": {"type": "string", "description": "The ID of the server."}
                },
                "required": ["server_id"]
            }
        }
    },
    # --- >>>> TASK 4: Define Schema for escalate_to_engineer ---
    {
        "type": "function",
        "function": {
            "name": "escalate_to_engineer",
            "description": "Escalates the issue to a human engineer when automated fixes fail or the error is unknown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server."},
                },
                "required": ["summary"]
            }
        }
    }
]

def run_it_agent(user_issue: str):
   print(f"\n ----- New Incident: {user_issue} ---")

   messages = [
        {"role": "system", "content": "You are a Level 1 IT Responder. Investigate server issues. "
                                      "If CPU or Memory is > 90%, restart the service. If logs show critical dependency errors (like connection refused) that a restart won't fix, escalate to an engineer."},
        {"role": "user", "content": user_issue}
    ]

   while True:
    print("\n AI Thinking....")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_msg = response.choices[0].message

    messages.append(response_msg.model_dump(exclude_none=True))

    if response_msg.tool_calls:
        for tool_call in response_msg.tool_calls:
           func_name = tool_call.function.name
           func_args = json.loads(tool_call.function.arguments)


           function_to_call = AVAILABLE_FUNCTIONS.get(func_name)

           if function_to_call:
              tool_output = function_to_call(**func_args)
              messages.append({
                  "role": "tool",
                  "tool_call_id": tool_call.id,
                  "name": tool_call.function.name,
                  "content": tool_output,
              })


    else:
       print(f"\n[FINAL RESPONSE]: {response_msg.content}")
       break