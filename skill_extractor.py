from collections import defaultdict
from llm_utils import ask_llm

def extract_ticket_info(issue, jira_client):
    comments = jira_client.comments(issue.key)
    comment_text = "\n".join([c.body for c in comments])

    return {
        "key": issue.key,
        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
        "summary": issue.fields.summary or "",
        "description": issue.fields.description or "",
        "acceptance_criteria": getattr(issue.fields, "customfield_12345", ""),
        "comments": comment_text
    }

def infer_skills_from_ticket(ticket, prompt_template):
    prompt = prompt_template.format(**ticket)
    return [s.strip().lower() for s in ask_llm(prompt).split(",") if s.strip()]

def infer_skills_from_closed_sprints(jira_client, board_id, prompt_template, last_n=2):
    all_skills = defaultdict(set)
    closed_sprints = jira_client.sprints(board_id, state='closed')[-last_n:]
    for sprint in closed_sprints:
        issues = jira_client.search_issues(f"sprint = {sprint.id}", maxResults=1000)
        for issue in issues:
            ticket = extract_ticket_info(issue, jira_client)
            skills = infer_skills_from_ticket(ticket, prompt_template)
            all_skills[ticket["assignee"]].update(skills)
    return {a: sorted(s) for a, s in all_skills.items()}
