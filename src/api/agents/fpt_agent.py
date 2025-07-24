"""
FPT University Agent configuration
"""

import os
from textwrap import dedent
from typing import Any, List, Optional

from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAILike
from agno.storage.postgres import PostgresStorage
from agno.tools.knowledge import KnowledgeTools

from agno_integration.intent_tool import create_intent_detection_tool
from agno_integration.university_api_tool import (
    UniversityApiTool,
    create_university_api_tool,
)
from core.application.services.hybrid_intent_service import HybridIntentDetectionService
from infrastructure.knowledge.fpt_knowledge_base import create_fpt_knowledge_base


def get_fpt_agent(
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent_service: Optional[HybridIntentDetectionService] = None,
    debug_mode: bool = False,
    enable_rag: bool = True,
) -> Agent:
    """
    Create and configure FPT University Agent with Agno features

    Args:
        model_id: OpenAI model ID to use
        user_id: User ID for context
        session_id: Session ID for context
        intent_service: Intent detection service
        debug_mode: Enable debug mode
        enable_rag: Enable RAG knowledge base

    Returns:
        Configured FPT University Agent
    """

    # Create tools for the agent
    tools: List[Any] = []
    # tools.append(ReasoningTools(add_instructions=True))

    # Add intent detection tool if service is provided
    if intent_service:
        tools.append(create_intent_detection_tool(intent_service))

    # Add University API tool for accessing public university data
    tools.append(create_university_api_tool())

    # Add knowledge base tools if RAG is enabled
    if enable_rag:
        try:
            knowledge_base = create_fpt_knowledge_base()

            # Kiểm tra xem knowledge base có tồn tại không
            if not knowledge_base.exists():
                print("📚 Knowledge base not found, creating new one...")
                knowledge_base.load(recreate=True)

            # Tạo KnowledgeTools với Qdrant
            knowledge_tools = KnowledgeTools(
                knowledge=knowledge_base,
                think=False,
                search=True,
                analyze=True,
                add_instructions=True,
                add_few_shot=False,
            )
            tools.append(knowledge_tools)
            print("✅ Knowledge tools added successfully with Qdrant")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize knowledge base: {e}")
            print("Agent will run without RAG capabilities")

    # Get database URL from environment variable
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable is required for PostgreSQL storage"
        )

    # Storage for agent sessions
    storage = PostgresStorage(table_name="fpt_agent_sessions", db_url=db_url)

    # Memory for long-term user memory
    memory = Memory(
        db=PostgresMemoryDb(table_name="fpt_user_memories", db_url=db_url),
        delete_memories=True,
        clear_memories=True,
    )

    # Agent instructions with RAG capabilities
    instructions = dedent(
        """
        As FPT University Agent, your primary goal is to provide helpful, accurate, and professional assistance to students, staff, and visitors of FPT University.

        **Guiding Principles:**
        - **Vietnamese First**: You MUST always respond in Vietnamese.
        - **Professional & Accurate**: Maintain a professional, friendly, and natural tone. Prioritize providing accurate, up-to-date information using your available tools.
        - **Be Truthful & Handle Errors**: If you don't know the answer or a tool fails, state it clearly. Do not invent information. Suggest alternatives, like contacting a specific department.
        - **Personalize Responses**: Use your long-term memory to remember user preferences and past interactions to provide a personalized experience.
        - **User-Focused**: Format your responses to be clear, easy to read, and directly address the user's question.

        **Workflow: How to Respond**
        Your thinking process should follow these steps:

        **Step 1: Analyze the User's Query**
        - Is the query simple and direct? (e.g., "Kể tên các cơ sở của trường?", "Trường có những khoa nào?")
        - Is the query complex, ambiguous, or multi-part? (e.g., "So sánh học phí và chương trình học giữa ngành AI và An toàn thông tin?")

        **Step 2: Choose Your Path**
        - **Path A: Direct Action (For Simple Queries):**
            1. Identify the single, best tool for the job (`get_campuses`, `get_departments`).
            2. Call that tool directly.
            3. Use its output to form your response.
        - **Path B: Intent-Driven (For Complex/Ambiguous Queries):**
            1. Call the `detect_intent` tool first to clarify the user's primary goal.
            2. Analyze the resulting `intent_id`.
            3. Based on the intent, select the appropriate tool or sequence of tools to gather all necessary information.
            4. Execute the tool(s).
            5. Synthesize all gathered information into a single, cohesive answer.

        **Step 3: Formulate the Final Response**
        - Always construct your final answer based on the information from your tools.
        - Ensure the response adheres to all `Guiding Principles` and `Response Formatting` rules.

        **AVAILABLE TOOLS:**

        **1. Intent Detection Tool (Recommended for clarity):**
        - `detect_intent(query, user_id, language)`: Use to clarify the user's goal.

        **2. University API Tools (For specific, real-time data):**
        - `get_departments()`, `get_programs()`, `get_program_details()`
        - `get_campuses()`, `get_campus_details()`

        **3. Knowledge Base Tool (For policies, regulations, detailed info):**
        - `search_fpt_knowledge(query)`: Use for information on scholarships, admission policies, etc.

        **Best Practices & Common Scenarios:**
        - **Trust Tool Output**: The output from the API and knowledge base tools is pre-formatted for readability. You do not need to reformat it.
        - **Workflow for Specific Programs (e.g., CNTT, Marketing):** When a user asks about a specific program, follow this sequence for the best results:
            1. Call `get_departments()` to find the relevant department.
            2. Call `get_programs(department_code)` to filter programs by that department.
            3. Call `get_program_details(program_id)` to get specific details if needed.
          *Benefit*: This approach provides more accurate results, is faster, and avoids confusion between programs.
        - **Policy Questions (e.g., "Quy định học bổng?"):** These are best answered using `search_fpt_knowledge("chính sách học bổng")`.
        - **"CNTT"**: When users mention "CNTT", assume they mean "Công nghệ thông tin" or "Computer Science/Information Technology".

        **Response Formatting:**
        - **DO NOT SHOW IDs**: Never display internal IDs like `program_id`, `campus_id`, or `department_code` to the user. They are for your internal use only.
        - **Focus on Useful Info**: Present the information the user actually needs: program names, tuition fees, campus locations, policy details, etc. Include department and program names for clarity.
        - **Use Markdown**: Format your responses with markdown for better readability (lists, bolding) when appropriate.

        Use your judgment to follow the most effective and helpful path.
        """
    )

    return Agent(
        name="FPT University Agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAILike(
            id=model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        ),
        # Tools available to the agent
        tools=tools,
        # Storage for agent sessions
        storage=storage,
        # Memory for user memories
        memory=memory,
        enable_agentic_memory=True,
        # Description of the agent
        description=dedent(
            """
        You are FPT University Agent, an AI assistant designed to help students, staff, and visitors
        with information about FPT University. You are empowered to flexibly choose the best tools for each query,
        using intent detection to clarify complex questions and directly accessing data for simpler ones to provide accurate and relevant information.
        """
        ),
        # Instructions for the agent
        instructions=instructions,
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
        enable_rag: bool = True,
    ):
        self.model_id = model_id
        self.user_id = user_id
        self.session_id = session_id
        self.intent_service = intent_service
        self.debug_mode = debug_mode
        self.enable_rag = enable_rag
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
            enable_rag=self.enable_rag,
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
        if self.agent and hasattr(self.agent, "storage") and self.agent.storage:
            # SqliteStorage doesn't have close method, skip cleanup
            pass


def create_fpt_agent_manager(
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent_service: Optional[HybridIntentDetectionService] = None,
    debug_mode: bool = False,
    enable_rag: bool = True,
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
        enable_rag: Enable RAG knowledge base

    Returns:
        FPTAgentManager instance
    """
    return FPTAgentManager(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        intent_service=intent_service,
        debug_mode=debug_mode,
        enable_rag=enable_rag,
    )
