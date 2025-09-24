"""
Boston Guide CrewAI Agent wrapped for Nanda Adapter
"""

import os
from crewai import Agent, Task, Crew, Process, LLM
from langchain_anthropic import ChatAnthropic
from nanda_adapter import NANDA

# ----------------------------
# Core agent setup
# ----------------------------
llm = ChatAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-haiku-20240307"   # or claude-3-sonnet if you want a stronger model
)

def create_introduction_task(user_choice, agent):
    base_intro = """
    Introduce yourself as Tong in 3-5 sentences. You are a Harvard M.S. Data Science student originally from Shenzhen, China,
    who studied in Beijing for college. You love street dance (choreography and K-pop), cooking and tasting food, city walks,
    traveling, exploring new things, artistic experiences, movies, and caring for plants and animals (especially dogs and birds).
    You bring warmth, curiosity, and creativity into conversations.
    """
    
    if user_choice == "1":
        description = base_intro + " Focus on your passion for food."
        expected_output = "Food-focused introduction."
    elif user_choice == "2":
        description = base_intro + " Focus on your love for activities and experiences."
        expected_output = "Activity-focused introduction."
    elif user_choice == "3":
        description = base_intro + " Provide a balanced introduction."
        expected_output = "Balanced introduction."
    else:
        raise ValueError("Invalid choice")

    return Task(description=description, expected_output=expected_output, agent=agent, max_iter=1)

def create_boston_guide_task(user_choice, agent, intro_task):
    base_requirements = """
    You are Tong. Based on your introduction, give personalized recommendations
    that align with YOUR interests and background as a Harvard Data Science student.
    Requirements:
    - Reference YOUR intro when explaining recommendations
    - Format as numbered Markdown lists
    - Each item must include ONE emoji and name in bold
    - Add 1-2 sentences explaining why it's perfect for Tong
    - Focus on Cambridge, Allston, Brighton, Boston proper, Brookline, and Somerville
    - Focus on budget-friendly student options
    """
    
    if user_choice == "1":
        description = base_requirements + " Recommend EXACTLY 3 restaurants."
        expected_output = "3 restaurants with explanations."
    elif user_choice == "2":
        description = base_requirements + " Recommend EXACTLY 3 activities."
        expected_output = "3 activities with explanations."
    elif user_choice == "3":
        description = base_requirements + " Recommend 3 restaurants AND 3 activities."
        expected_output = "3 restaurants and 3 activities with explanations."
    else:
        raise ValueError("Invalid choice")

    return Task(description=description, expected_output=expected_output,
                agent=agent, max_iter=1, context=[intro_task])

# ----------------------------
# Core pipeline function
# ----------------------------
def run_boston_agent(user_choice: str) -> str:
    """Run the CrewAI pipeline for choice 1/2/3 and return results as a string."""

    # Agent 1: Self Introduction
    self_intro_agent = Agent(
        role="Tong - Harvard Data Science Student",
        goal="Provide a warm introduction based on user choice",
        backstory="Tong, Harvard M.S. Data Science student from Shenzhen, brings warmth, curiosity, and creativity.",
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    # Agent 2: Boston Guide
    boston_guide_agent = Agent(
        role="Tong - Personal Boston Recommender",
        goal="Provide personalized Boston recommendations",
        backstory="Tong recommends restaurants and activities based on personal background and interests.",
        verbose=False,
        allow_delegation=False,
        llm=llm
    )

    # Tasks
    intro_task = create_introduction_task(user_choice, self_intro_agent)
    recommendation_task = create_boston_guide_task(user_choice, boston_guide_agent, intro_task)

    # Crew
    crew = Crew(
        agents=[self_intro_agent, boston_guide_agent],
        tasks=[intro_task, recommendation_task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()
    intro_result = intro_task.output.raw if hasattr(intro_task, "output") else "Intro done"

    return f"👋 Introduction\n{intro_result}\n\n📍 Recommendations\n{result}"

# ----------------------------
# Nanda Adapter wrapper
# ----------------------------
def improvement(message_text: str) -> str:
    """Map free text → choice and run the agent."""
    msg = message_text.lower().strip()

    # Direct handling of "both"
    if msg == "both":
        return run_boston_agent("3")

    # keywords
    food_keywords = ["food", "restaurant", "restaurants", "eat", "dining"]
    activity_keywords = ["activity", "activities", "things to do", "events", "places to go"]

    # check flags
    food_flag = any(word in msg for word in food_keywords)
    activity_flag = any(word in msg for word in activity_keywords)

    if food_flag and activity_flag:
        choice = "3"
    elif food_flag:
        choice = "1"
    elif activity_flag:
        choice = "2"
    else:
        return "❌ Sorry, I don’t understand. Please ask for food, activities, or both."

    return run_boston_agent(choice)


# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    nanda = NANDA(improvement)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    domain = os.getenv("DOMAIN_NAME")
    nanda.start_server_api(anthropic_key, domain)