
def calculate_capacity(team):
    velocity_per_point = team.get("velocity_per_point", 4)
    total_hours = sum(member["available_hours"] for member in team["members"])
    return total_hours // velocity_per_point
