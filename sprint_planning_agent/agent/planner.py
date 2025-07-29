
def plan_sprint(stories, team):
    assignments = {member["name"]: [] for member in team["members"]}
    member_cycle = list(assignments.keys())
    idx = 0
    for story in stories:
        assignee = member_cycle[idx % len(member_cycle)]
        assignments[assignee].append(story)
        idx += 1
    return assignments
