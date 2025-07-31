from jira import JIRA
import os

def get_jira_client():
    jira_url = os.getenv("JIRA_URL", "https://your-domain.atlassian.net")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    return JIRA(server=jira_url, basic_auth=(jira_user, jira_token))
