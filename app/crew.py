"""
Simplified Crew Assembly - 4 agents in sequential pipeline
"""
import logging
from crewai import Crew, Task, Process

from app.agents import input_processor, content_finder, activity_builder, formatter
from app.models import ActivityDetails

logger = logging.getLogger(__name__)


def create_activity_crew():
    """
    Create and return the 4-agent crew for activity generation.

    Returns:
        Crew: Configured crew with 4 agents and tasks
    """
    logger.info("Creating activity generation crew...")

    # Task 1: Collect and confirm details
    collect_task = Task(
        description="""Collect activity details from user input and get confirmation.

        User input: {user_input}

        Extract:
        - Main topic (exact phrase from user)
        - Age group (middle or teen)
        - Duration (30-60 minutes)
        - Activity type
        - Main values/themes

        Present summary and get explicit confirmation before proceeding.""",

        agent=input_processor,
        expected_output="ActivityDetails JSON with confirmed details"
    )

    # Task 2: Find content
    find_content_task = Task(
        description="""Find relevant content for the activity:

        1. Search agadah.org.il for 2-3 relevant stories
        2. Search game database for 2-3 game ideas
        3. Return list with titles, links, and brief relevance notes

        Use the confirmed details from previous task.""",

        agent=content_finder,
        expected_output="List of stories from agadah.org.il and game ideas with explanations",
        context=[collect_task]
    )

    # Task 3: Build activity
    build_activity_task = Task(
        description="""Create complete activity plan:

        Structure: 4-5 sections
        - Opening (game/icebreaker)
        - Story (from research results)
        - Main activity (game/quiz/creation)
        - Closing (summary)

        Include:
        - Step-by-step instructions
        - Time allocations
        - Materials needed
        - Discussion questions
        - Story links
        - Facilitator notes

        Self-review for:
        - Age appropriateness
        - Engagement level
        - Time management
        - Story integration
        - Safety (especially for teens: must include physical component)""",

        agent=activity_builder,
        expected_output="Complete ActivityReport JSON with all sections",
        context=[collect_task, find_content_task]
    )

    # Task 4: Format output
    format_task = Task(
        description="""Convert activity plan to readable Hebrew markdown:

        Format:
        1. Main title and overview
        2. Materials list
        3. Numbered activity sections with:
           - Section name
           - Time estimate
           - Step-by-step instructions
           - Discussion questions
        4. Story links (credit: אתר אגדה)
        5. Facilitator preparation notes

        Use clear Hebrew, markdown formatting, professional style.""",

        agent=formatter,
        expected_output="Formatted Hebrew markdown text ready for educators",
        context=[build_activity_task]
    )

    # Assemble crew
    crew = Crew(
        agents=[input_processor, content_finder, activity_builder, formatter],
        tasks=[collect_task, find_content_task, build_activity_task, format_task],
        process=Process.sequential,
        verbose=True,
        memory=False,  # Disable memory to prevent cross-conversation pollution
        max_execution_time=1800  # 30 minutes max
    )

    logger.info("Crew created successfully with 4 agents")
    return crew
