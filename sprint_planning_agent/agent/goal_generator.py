
def generate_goal(stories):
    topics = [story["title"] for story in stories]
    return "Complete core functionalities including: " + ", ".join(topics[:3]) + "..."
