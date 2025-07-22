"""
FPT University Agent configuration
"""

import os
from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAILike
from agno.tools.reasoning import ReasoningTools
from agno.storage.sqlite import SqliteStorage
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

from agno_integration.intent_tool import create_intent_detection_tool
from core.application.services.hybrid_intent_service import HybridIntentDetectionService


def get_fpt_agent(
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent_service: Optional[HybridIntentDetectionService] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Create and configure FPT University Agent with Agno features

    Args:
        model_id: OpenAI model ID to use
        user_id: User ID for context
        session_id: Session ID for context
        intent_service: Intent detection service
        debug_mode: Enable debug mode

    Returns:
        Configured FPT University Agent
    """

    # Create intent detection tool if service is provided
    # According to Agno docs: tools: Optional[List[Union[Toolkit, Callable, Function, Dict]]] = None
    tools = []
    tools.append(ReasoningTools(add_instructions=True))
    if intent_service:
        tools.append(create_intent_detection_tool(intent_service))

    # Storage for agent sessions
    storage = SqliteStorage(
        table_name="fpt_agent_sessions",
        db_file="tmp/fpt_agent.db"
    )

    # Memory for long-term user memory
    memory = Memory(
        db=SqliteMemoryDb(
            table_name="fpt_user_memories",
            db_file="tmp/fpt_memory.db"
        ),
        delete_memories=True,
        clear_memories=True,
    )

    return Agent(
        name="FPT University Agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAILike(
            id=model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        ),
        # Tools available to the agent
        tools=tools,
        # Storage for agent sessions
        storage=storage,
        # Memory for user memories
        memory=memory,
        enable_agentic_memory=True,
        # Description of the agent
        description=dedent("""
        You are FPT University Agent, an AI assistant designed to help students, staff, and visitors
        with information about FPT University. You have access to intent detection capabilities and
        reasoning tools to provide thoughtful, accurate responses.
        """),
        # Instructions for the agent
        instructions=dedent("""
        As FPT University Agent, your goal is to provide helpful, accurate, and professional assistance
        to students, staff, and visitors of FPT University.

        Your capabilities include:
        - Intent detection to understand user queries and their purpose
        - Reasoning to provide thoughtful, well-structured responses
        - Access to FPT University knowledge base and information
        - Long-term memory to remember user preferences and past interactions

        Guidelines for your responses:
        1. **Understand the Query**: Use intent detection to understand what the user is asking for
        2. **Provide Accurate Information**: Give precise, up-to-date information about FPT University
        3. **Be Professional**: Maintain a helpful and professional tone
        4. **Use Reasoning**: For complex questions, break down your thinking process
        5. **Be Concise**: Provide clear, direct answers while being comprehensive
        6. **Cite Sources**: When possible, reference official FPT University sources
        7. **Remember Users**: Use your memory to personalize responses based on past interactions

        Common topics you can help with:
        - Academic programs and courses
        - Admission requirements and procedures
        - Campus facilities and services
        - Student life and activities
        - Faculty and staff information
        - Research and innovation
        - International partnerships
        - Events and news

        Always be truthful about what you know and don't know. If you're unsure about specific details,
        suggest contacting the relevant department or checking the official FPT University website.
        """),
        # Add state in messages for dynamic content
        add_state_in_messages=True,
        # Add history to messages
        add_history_to_messages=True,
        # Number of history responses
        num_history_responses=5,
        # Format responses using markdown
        markdown=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Show tool calls in responses
        show_tool_calls=True,
        # Show debug logs
        debug_mode=debug_mode,
    )
