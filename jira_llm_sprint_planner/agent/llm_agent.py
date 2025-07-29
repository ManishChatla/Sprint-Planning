
from langchain.chat_models import ChatOpenAI

class JiraSprintLLMAgent:
    def __init__(self, tickets, team_data, model_name="gpt-4"):
        self.llm = ChatOpenAI(temperature=0.2, model=model_name)
        self.tickets = tickets
        self.team = team_data

    def generate_plan(self):
        prompt = self._build_prompt()
        response = self.llm.predict(prompt)
        return response

    def _build_prompt(self):
        ticket_info = "\n".join([
            f"{t['key']}: {t['summary']} - {t['description']} [{t['points']} pts]"
            for t in self.tickets
        ])
        team_info = "\n".join([
            f"{m['name']}: Skills({', '.join(m['skills'])}), Available({m['available_points']} pts)"
            for m in self.team["members"]
        ])

        return f"""
You are a smart sprint planning assistant.

Given:
1. Jira ticket descriptions with story points
2. Team members with skills and available capacity

Assign the tickets based on:
- Required skills inferred from description
- Available capacity (story points)
- Best matching person per task

Tickets:
{ticket_info}

Team:
{team_info}

Return JSON:
{{ "assignments": [{{ "ticket": "JIRA-101", "assigned_to": "Alice" }}] }}
"""
