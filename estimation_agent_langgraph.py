# pip install langgraph langchain-openai
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

class EstimationState(TypedDict):
    historical: List[Dict[str, Any]]
    backlog: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    approved: bool

def fetch_history(state: EstimationState):
    state["historical"] = mcp_invoke(MCP_TOOL_SEARCH_CLOSED)
    return state

def fetch_backlog(state: EstimationState):
    state["backlog"] = mcp_invoke(MCP_TOOL_SEARCH_BACKLOG)
    return state

def estimate(state: EstimationState):
    state["suggestions"] = run_estimation(state["historical"], state["backlog"])
    print("\n--- Suggested Estimates ---")
    pretty_review(state["suggestions"])
    return state

def wait_for_human(state: EstimationState):
    _ = input("\nReview the table above. Press Enter to edit, or type 'ok' to approve: ").strip().lower()
    if _ != "ok":
        state["suggestions"] = interactive_edit(state["suggestions"])
    ans = input("Approve updates? (yes/no): ").strip().lower()
    state["approved"] = ans in ("yes", "y")
    return state

def update_jira(state: EstimationState):
    if state.get("approved"):
        push_updates(state["suggestions"])
        print("✅ Jira updated.")
    else:
        print("❎ Not approved. Skipping updates.")
    return state

workflow = StateGraph(EstimationState)
workflow.add_node("fetch_history", fetch_history)
workflow.add_node("fetch_backlog", fetch_backlog)
workflow.add_node("estimate", estimate)
workflow.add_node("wait_for_human", wait_for_human)
workflow.add_node("update_jira", update_jira)

workflow.set_entry_point("fetch_history")
workflow.add_edge("fetch_history", "fetch_backlog")
workflow.add_edge("fetch_backlog", "estimate")
workflow.add_edge("estimate", "wait_for_human")
workflow.add_edge("wait_for_human", "update_jira")
workflow.add_edge("update_jira", END)

app = workflow.compile()

# Run:
state = {"historical": [], "backlog": [], "suggestions": [], "approved": False}
app.invoke(state)
