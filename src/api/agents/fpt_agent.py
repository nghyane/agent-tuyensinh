"""
FPT University Agent configuration
"""

import os
from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAILike
from agno.tools.reasoning import ReasoningTools
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory

from agno_integration.intent_tool import create_intent_detection_tool
from agno_integration.university_api_tool import create_university_api_tool, UniversityApiTool
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

    # Create tools for the agent
    # According to Agno docs: tools: Optional[List[Union[Toolkit, Callable, Function, Dict]]] = None
    tools = []
    tools.append(ReasoningTools(add_instructions=True))

    # Add intent detection tool if service is provided
    if intent_service:
        tools.append(create_intent_detection_tool(intent_service))

    # Add University API tool for accessing public university data
    tools.append(create_university_api_tool())

    # Get database URL from environment variable
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required for PostgreSQL storage")
    
    # Storage for agent sessions
    storage = PostgresStorage(
        table_name="fpt_agent_sessions",
        db_url=db_url
    )

    # Memory for long-term user memory
    memory = Memory(
        db=PostgresMemoryDb(
            table_name="fpt_user_memories",
            db_url=db_url
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
        - Access to FPT University official API for real-time data
        - Information about departments, programs, campuses, and fees
        - Long-term memory to remember user preferences and past interactions

        Guidelines for your responses:
        1. **Understand the Query**: Use intent detection to understand what the user is asking for
        2. **Use Official Data**: Always use the FPT API tool to get real-time, accurate information
        3. **Be Professional**: Maintain a helpful and professional tone
        4. **Use Reasoning**: For complex questions, break down your thinking process
        5. **Be Comprehensive**: Provide detailed information when available from the API
        6. **Handle Errors Gracefully**: If API is unavailable, inform users and suggest alternatives
        7. **Remember Users**: Use your memory to personalize responses based on past interactions

        **IMPORTANT WORKFLOW FOR TUITION INQUIRIES (học phí):**
        When users ask about tuition fees for a specific program (e.g., "học phí ngành CNTT"):
        1. First, use intent detection to confirm this is a tuition inquiry
        2. Use get_departments() to find relevant departments (e.g., CNTT relates to IT/Computer Science departments)
        3. Use get_programs(department_code) to get programs from the relevant department
        4. Use get_program_details(program_id) to get specific tuition and fee information
        5. Provide comprehensive information including program details and costs

        **WORKFLOW FOR PROGRAM INFORMATION:**
        When users ask about academic programs:
        1. Use intent detection to understand the specific inquiry type
        2. If asking about general programs: use get_programs() to list available programs
        3. If asking about specific program: use get_departments() first, then get_programs() with department filter
        4. For detailed info: use get_program_details() with specific program ID
        5. Always provide program code, duration, department, and English name when available

        **WORKFLOW FOR CAMPUS INFORMATION:**
        When users ask about facilities, locations, or campus details:
        1. Use get_campuses() to list all campuses
        2. Use get_campus_details(campus_id) for specific campus information
        3. Include contact information, facilities, and programs offered at each campus

        Common topics you can help with:
        - Academic programs and courses (use get_programs, get_program_details)
        - Tuition fees and costs (use department → programs → program details workflow)
        - Campus facilities and locations (use get_campuses, get_campus_details)
        - Department information (use get_departments)
        - Admission requirements and procedures
        - Student life and activities
        - Faculty and staff information
        - Research and innovation
        - International partnerships
        - Events and news

        **IMPORTANT NOTES:**
        - Always use the API tools in the correct sequence for complex queries
        - For tuition inquiries, you MUST get program details as tuition is program-specific
        - When mentioning program names like "CNTT", explain that this refers to specific departments/programs
        - Provide both Vietnamese and English names when available
        - Include program codes and department information for clarity

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


class FPTAgentManager:
    """
    Context manager for FPT Agent with proper cleanup of resources
    """

    def __init__(
        self,
        model_id: str = "gpt-4o",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intent_service: Optional[HybridIntentDetectionService] = None,
        debug_mode: bool = False,
    ):
        self.model_id = model_id
        self.user_id = user_id
        self.session_id = session_id
        self.intent_service = intent_service
        self.debug_mode = debug_mode
        self.agent: Optional[Agent] = None
        self.university_api_tool: Optional[UniversityApiTool] = None

    async def __aenter__(self) -> Agent:
        """Initialize agent with proper resource management"""
        self.agent = get_fpt_agent(
            model_id=self.model_id,
            user_id=self.user_id,
            session_id=self.session_id,
            intent_service=self.intent_service,
            debug_mode=self.debug_mode,
        )

        # Find University API tool for cleanup later
        for tool in self.agent.tools or []:
            if isinstance(tool, UniversityApiTool):
                self.university_api_tool = tool
                break

        return self.agent

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup agent resources"""
        if self.university_api_tool:
            await self.university_api_tool.close()

        # Close agent storage if available
        if self.agent and hasattr(self.agent, 'storage') and self.agent.storage:
            # SqliteStorage doesn't have close method, skip cleanup
            pass


def create_fpt_agent_manager(
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent_service: Optional[HybridIntentDetectionService] = None,
    debug_mode: bool = False,
) -> FPTAgentManager:
    """
    Create FPT Agent Manager with auto-cleanup

    Usage:
        async with create_fpt_agent_manager() as agent:
            response = await agent.run("Học phí ngành CNTT bao nhiêu?")

    Args:
        model_id: OpenAI model ID to use
        user_id: User ID for context
        session_id: Session ID for context
        intent_service: Intent detection service
        debug_mode: Enable debug mode

    Returns:
        FPTAgentManager instance
    """
    return FPTAgentManager(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        intent_service=intent_service,
        debug_mode=debug_mode,
    )
