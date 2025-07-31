from jira import JIRA
import os

def get_jira_client():
    return JIRA(
        server=os.getenv("JIRA_URL"),
        basic_auth=(os.getenv("JIRA_USER"), os.getenv("JIRA_TOKEN"))
    )

def get_active_sprint_issues(jira, board_id):
    active_sprint = [s for s in jira.sprints(board_id) if s.state == "active"][-1]
    return jira.search_issues(f"sprint = {active_sprint.id}", maxResults=100)
