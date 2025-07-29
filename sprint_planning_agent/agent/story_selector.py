
def select_stories(backlog, capacity_points):
    sorted_backlog = sorted(backlog, key=lambda x: x['priority'], reverse=True)
    selected = []
    total = 0
    for story in sorted_backlog:
        if total + story['points'] <= capacity_points:
            selected.append(story)
            total += story['points']
    return selected
