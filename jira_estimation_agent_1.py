# pip install langchain-openai pydantic jsonschema tabulate
import json, os, sys
from copy import deepcopy
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from tabulate import tabulate
from langchain_openai import ChatOpenAI

# --------------------------
# CONFIG
# --------------------------
OPENAI_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
TEMPERATURE = float(os.getenv("LLM_TEMP", "0.2"))
# Your Jira MCP tool names / params (adapt to your MCP server)
MCP_TOOL_SEARCH_CLOSED = "jira.search_closed_last_two_sprints"
MCP_TOOL_SEARCH_BACKLOG = "jira.search_backlog_unestimated"
MCP_TOOL_UPDATE_POINTS = "jira.update_story_points"
STORY_POINTS_FIELD_ID = os.getenv("JIRA_SP_FIELD_ID", "customfield_10016")  # adjust to your Jira

ALLOWED_POINTS = [1, 2, 3, 5, 8, 13, 20]

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=TEMPERATURE)

# --------------------------
# MCP CLIENT PLACEHOLDER
# Replace these with your Jira MCP server invocations.
# --------------------------
def mcp_invoke(tool: str, **kwargs) -> Any:
    """
    Replace with real MCP invocation, e.g.:
    return mcp_client.call(tool, kwargs)
    """
    if tool == MCP_TOOL_SEARCH_CLOSED:
        # Return last 2 sprints' closed issues with SPs
        return [
            {"ticket_key": "WEB-101", "issue_type": "Story",
             "summary": "Implement login API",
             "description": "JWT auth + rate limit",
             "labels": ["backend", "auth"], "components": ["Auth Service"],
             "linked_issues": [], "subtasks": 3, "priority": "High",
             "epic_link": "EPIC-12", "story_points": 8, "cycle_time_days": 3},

            {"ticket_key": "WEB-110", "issue_type": "Bug",
             "summary": "Fix dashboard CSS glitch",
             "description": "Buttons misaligned in Safari",
             "labels": ["frontend", "ui"], "components": ["Dashboard"],
             "linked_issues": [], "subtasks": 1, "priority": "Medium",
             "epic_link": "EPIC-10", "story_points": 2, "cycle_time_days": 1},
        ]
    if tool == MCP_TOOL_SEARCH_BACKLOG:
        # Return backlog needing SP (story_points missing)
        return [
            {"ticket_key": "WEB-202", "issue_type": "Story",
             "summary": "Add password reset flow",
             "description": "Email reset link + secure token",
             "labels": ["backend", "auth", "email"], "components": ["Auth Service", "Email Service"],
             "linked_issues": ["WEB-101"], "subtasks": 2, "priority": "Medium", "epic_link": "EPIC-12"},

            {"ticket_key": "WEB-203", "issue_type": "Story",
             "summary": "Improve dashboard charts",
             "description": "Filters + new line chart, export CSV",
             "labels": ["frontend", "ui"], "components": ["Dashboard"],
             "linked_issues": [], "subtasks": 2, "priority": "Low", "epic_link": "EPIC-10"},
        ]
    if tool == MCP_TOOL_UPDATE_POINTS:
        # kwargs: ticket_key, points, field_id
        print(f"[MCP] Updating {kwargs['ticket_key']} -> {kwargs['points']} SP via {tool} ({kwargs['field_id']})")
        return {"status": "ok"}
    raise NotImplementedError(f"No mock for tool {tool}")

# --------------------------
# Output schema & validation
# --------------------------
class EstimationItem(BaseModel):
    ticket_key: str
    predicted_story_points: int = Field(..., description="One of allowed buckets")
    reasoning: str

class EstimationOutput(BaseModel):
    __root__: List[EstimationItem]

def force_to_bucket(n: Any) -> int:
    try:
        n = int(round(float(n)))
    except Exception:
        return 3
    # snap to nearest allowed bucket
    return min(ALLOWED_POINTS, key=lambda x: abs(x - n))

def validate_estimations(raw_text: str) -> List[Dict[str, Any]]:
    # try parse JSON array or object-wrapped array
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "results" in data:
            data = data["results"]
        if isinstance(data, dict):
            data = [data]
    except Exception:
        # Last-resort: extract JSON block
        start = raw_text.find('[')
        end = raw_text.rfind(']')
        if start != -1 and end != -1:
            data = json.loads(raw_text[start:end+1])
        else:
            raise ValueError("LLM did not return JSON.")
    # coerce / validate
    for item in data:
        item["predicted_story_points"] = force_to_bucket(item.get("predicted_story_points"))
    try:
        EstimationOutput(__root__=data)
    except ValidationError as e:
        raise ValueError(f"Invalid estimation format: {e}")
    return data

# --------------------------
# Prompt (fits what we designed earlier)
# --------------------------
SYSTEM_PROMPT = """You are an Agile Estimation Assistant that assigns story points to Jira backlog tickets.
Use historical closed tickets from the last two sprints to predict story points for new backlog tickets.
Story points reflect relative effort/complexity. Use allowed buckets: 1, 2, 3, 5, 8, 13, 20.
Output strict JSON (array of objects), no commentary.
"""

USER_PROMPT_TEMPLATE = """
Historical Closed Tickets:
{historical}

Backlog Tickets to Estimate:
{backlog}

Task:
For each backlog ticket:
1) Compare with historical tickets (scope, complexity, risk, tech area).
2) Assign story points using allowed buckets only: 1,2,3,5,8,13,20.
3) Provide a short reasoning.
Return JSON ONLY in this shape:
[
  {{
    "ticket_key": "<KEY>",
    "predicted_story_points": <number>,
    "reasoning": "<why>"
  }}
]
"""

def run_estimation(historical: List[Dict[str, Any]], backlog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    user_prompt = USER_PROMPT_TEMPLATE.format(
        historical=json.dumps(historical, ensure_ascii=False, indent=2),
        backlog=json.dumps(backlog, ensure_ascii=False, indent=2)
    )
    msg = [{"role": "system", "content": SYSTEM_PROMPT},
           {"role": "user", "content": user_prompt}]
    raw = llm.invoke(msg).content
    return validate_estimations(raw)

def pretty_review(estimations: List[Dict[str, Any]]) -> None:
    rows = [(e["ticket_key"], e["predicted_story_points"], e["reasoning"]) for e in estimations]
    print("\nProposed Estimates (review & edit if needed):\n")
    print(tabulate(rows, headers=["Ticket", "SP", "Reasoning"], tablefmt="github"))

def interactive_edit(estimations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edited = deepcopy(estimations)
    while True:
        cmd = input("\nEdit? (format: KEY=VALUE  or 'ok' to continue, 'list' to view): ").strip()
        if cmd.lower() in ("ok", "y", "yes", ""):
            return edited
        if cmd.lower() == "list":
            pretty_review(edited); continue
        if "=" in cmd:
            key, val = [x.strip() for x in cmd.split("=", 1)]
            # find and update
            found = False
            for item in edited:
                if item["ticket_key"].upper() == key.upper():
                    item["predicted_story_points"] = force_to_bucket(val)
                    print(f"Set {key} -> {item['predicted_story_points']}"); found = True; break
            if not found:
                print("Ticket not in suggestions.")
        else:
            print("Invalid input. Use KEY=VALUE, or 'ok'.")

def push_updates(estimations: List[Dict[str, Any]]) -> None:
    for e in estimations:
        mcp_invoke(MCP_TOOL_UPDATE_POINTS,
                   ticket_key=e["ticket_key"],
                   points=e["predicted_story_points"],
                   field_id=STORY_POINTS_FIELD_ID)

def main():
    print("Step 1) Fetching historical closed tickets...")
    historical = mcp_invoke(MCP_TOOL_SEARCH_CLOSED)

    print("Step 2) Fetching backlog tickets (unestimated)...")
    backlog = mcp_invoke(MCP_TOOL_SEARCH_BACKLOG)
    if not backlog:
        print("No backlog tickets needing estimation. Done."); sys.exit(0)

    print("Step 3) Generating LLM estimates...")
    suggestions = run_estimation(historical, backlog)
    pretty_review(suggestions)

    print("\nStep 4) Human review (edit any SP buckets if you disagree).")
    final = interactive_edit(suggestions)

    confirm = input("\nApprove updates to Jira? (yes/no): ").strip().lower()
    if confirm in ("yes", "y"):
        print("Step 5) Updating Jira via MCP...")
        push_updates(final)
        print("✅ Done.")
    else:
        print("❎ Skipped updates. Nothing changed.")

if __name__ == "__main__":
    main()
