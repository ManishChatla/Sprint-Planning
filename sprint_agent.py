from agent.tools.jira_tools import get_active_sprint_issues, get_jira_client
from agent.tools.skill_extractor import infer_skills_from_closed_sprints
from agent.tools.ticket_assigner import assign_or_split_ticket
import os

def run_sprint_planner():
    jira = get_jira_client()
    board_id = int(os.getenv("JIRA_BOARD_ID", "123"))

    # Get team skillsets using closed sprint history
    with open("prompts/skill_inference.txt") as f:
        skill_prompt = f.read()
    team_skills = infer_skills_from_closed_sprints(jira, board_id, skill_prompt)

    # Simulate availability
    user_availability = {user: 5 for user in team_skills.keys()}

    # Fetch active sprint tickets
    issues = get_active_sprint_issues(jira, board_id)

    # Process each ticket
    for issue in issues:
        assign_or_split_ticket(issue, team_skills, user_availability, jira)

if __name__ == "__main__":
    run_sprint_planner()
