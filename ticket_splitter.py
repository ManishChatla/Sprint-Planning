from llm_utils import ask_llm

def get_required_skills_from_ticket(ticket):
    with open("prompts/ticket_skill_requirements.txt") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(**ticket)
    response = ask_llm(prompt)
    return [s.strip().lower() for s in response.split(",") if s.strip()]
