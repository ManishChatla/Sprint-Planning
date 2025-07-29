
from jira import JIRA

def fetch_sprint_tickets(jira_url, project_key, board_id, auth):
    jira = JIRA(server=jira_url, basic_auth=auth)
    sprint = jira.sprints(board_id)[-1]
    jql = f'project={project_key} AND sprint={sprint.id} AND status!=Done'
    issues = jira.search_issues(jql, maxResults=100)
    return [{
        "key": issue.key,
        "summary": issue.fields.summary,
        "description": issue.fields.description,
        "points": getattr(issue.fields, "customfield_10002", 3)
    } for issue in issues]

def assign_tickets(jira_url, auth, assignments):
    jira = JIRA(server=jira_url, basic_auth=auth)
    for item in assignments["assignments"]:
        issue = jira.issue(item["ticket"])
        jira.assign_issue(issue, item["assigned_to"])
