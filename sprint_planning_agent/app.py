
from agent.story_selector import select_stories
from agent.team_capacity import calculate_capacity
from agent.goal_generator import generate_goal
from agent.planner import plan_sprint
import json

# Load data
backlog = json.load(open('data/backlog.json'))
team = json.load(open('data/team.json'))

# Step 1: Calculate team capacity
capacity = calculate_capacity(team)

# Step 2: Select stories based on priority and dependencies
selected_stories = select_stories(backlog, capacity)

# Step 3: Plan assignments
assignments = plan_sprint(selected_stories, team)

# Step 4: Generate sprint goal
sprint_goal = generate_goal(selected_stories)

# Output result
print("\n✅ Suggested Sprint Stories:")
for story in selected_stories:
    print(f"- {story['title']} [{story['points']} pts]")

print("\n👥 Task Assignments:")
for member, tasks in assignments.items():
    print(f"{member}: {[t['title'] for t in tasks]}")

print("\n🎯 Sprint Goal:")
print(sprint_goal)
