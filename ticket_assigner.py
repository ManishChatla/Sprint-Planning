from agent.tools.ticket_splitter import get_required_skills_from_ticket
from jira import Issue

def assign_or_split_ticket(issue: Issue, team_skills, user_availability, jira):
    ticket = {
        "key": issue.key,
        "summary": issue.fields.summary,
        "description": issue.fields.description or ""
    }

    required_skills = get_required_skills_from_ticket(ticket)
    skill_to_user = {}

    for skill in required_skills:
        for user, skills in team_skills.items():
            if skill in skills and user_availability.get(user, 0) > 0:
                skill_to_user[skill] = user
                user_availability[user] -= 1
                break

    unique_users = set(skill_to_user.values())
    if len(unique_users) == 1:
        assignee = list(unique_users)[0]
        jira.assign_issue(issue, assignee)
        print(f"✅ Assigned {issue.key} to {assignee}")
    else:
        for skill, user in skill_to_user.items():
            subtask_fields = {
                "project": {"key": issue.fields.project.key},
                "parent": {"key": issue.key},
                "summary": f"{ticket['summary']} – {skill.upper()} Task",
                "description": f"Subtask for {skill}\n\n{ticket['description']}",
                "issuetype": {"name": "Sub-task"},
                "assignee": {"name": user}
            }
            subtask = jira.create_issue(fields=subtask_fields)
            print(f"🔧 Created subtask {subtask.key} for {skill}, assigned to {user}")
