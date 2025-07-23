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
        with information about FPT University. You have access to intent detection capabilities,
        reasoning tools, and real-time university data to provide thoughtful, accurate responses.
        You can flexibly choose the most appropriate tools based on user queries.
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
        1. **Understand the Query**: Use intent detection when you need to understand the user's intent clearly
        2. **Use Official Data**: Always use the FPT API tools to get real-time, accurate information
        3. **Be Professional**: Maintain a helpful and professional tone
        4. **Use Reasoning**: For complex questions, break down your thinking process
        5. **Be Comprehensive**: Provide detailed information when available from the API
        6. **Handle Errors Gracefully**: If API is unavailable, inform users and suggest alternatives
        7. **Remember Users**: Use your memory to personalize responses based on past interactions

        **AVAILABLE TOOLS:**

        **Intent Detection Tool:**
        - detect_intent(query, user_id, language): Phát hiện ý định của người dùng
        - Sử dụng khi cần hiểu rõ intent của user query
        - Trả về intent ID, confidence, và suggestions

        **University API Tools:**
        - get_departments(limit, offset): Lấy danh sách khoa/phòng ban
        - get_programs(department_code, limit, offset): Lấy danh sách chương trình học
        - get_program_details(program_id): Lấy chi tiết chương trình học cụ thể
        - get_campuses(year, limit, offset): Lấy danh sách campus
        - get_campus_details(campus_id, year): Lấy chi tiết campus cụ thể

        **FLEXIBLE WORKFLOW APPROACH:**
        - Không cần tuân theo workflow cứng nhắc
        - Chọn tool phù hợp dựa trên context của câu hỏi
        - Có thể gọi trực tiếp tool cần thiết mà không cần qua intent detection
        - Sử dụng reasoning để quyết định tool nào cần dùng

        **OPTIMIZED WORKFLOW FOR SPECIFIC PROGRAMS:**
        - Khi user hỏi về ngành cụ thể (CNTT, Marketing, Business, etc.):
          1. get_departments() → tìm department phù hợp
          2. get_programs(department_code) → lọc programs theo department
          3. get_program_details(program_id) → lấy chi tiết nếu cần
        - Lợi ích: Kết quả chính xác hơn, nhanh hơn, tránh confusion

        **COMMON USE CASES:**

        **Học phí và chương trình học:**
        - Khi hỏi về học phí ngành cụ thể (như "CNTT"): 
          1. Dùng get_departments() để tìm department liên quan
          2. Dùng get_programs(department_code) để lọc theo department
          3. Dùng get_program_details(program_id) để lấy chi tiết học phí
        - Khi hỏi về tất cả ngành: dùng get_programs() không có filter
        - Khi cần chi tiết: dùng get_program_details() với program_id

        **Thông tin campus:**
        - Khi hỏi về campus: dùng get_campuses() để xem danh sách
        - Khi hỏi chi tiết campus: dùng get_campus_details() với campus_id

        **Thông tin khoa:**
        - Khi hỏi về khoa: dùng get_departments() để xem danh sách

        **IMPORTANT NOTES:**
        - Các tools đã được format sẵn, trả về text đẹp và dễ đọc
        - Không cần format lại kết quả từ tools
        - Khi user hỏi về "CNTT", hiểu là Computer Science/Information Technology
        - Luôn cung cấp thông tin bằng cả tiếng Việt và tiếng Anh khi có sẵn
        - Bao gồm mã chương trình và thông tin khoa để rõ ràng
        - **QUAN TRỌNG**: Mỗi item trong danh sách đều có ID để lấy chi tiết
        - Sử dụng ID từ danh sách để gọi get_program_details() hoặc get_campus_details()
        - **TỐI ƯU HÓA**: Khi hỏi về ngành cụ thể, luôn tìm department trước để lọc chính xác

        **EXAMPLES:**
        - User: "Học phí ngành CNTT bao nhiêu?" → get_departments() → get_programs(department_code) → get_program_details(program_id)
        - User: "Có những campus nào?" → get_campuses()
        - User: "Chi tiết campus Hà Nội" → get_campus_details(campus_id)
        - User: "Các khoa của trường" → get_departments()
        - User: "Chi tiết chương trình ABC" → get_program_details(program_id)
        - User: "Ngành CNTT có những chương trình gì?" → get_departments() → get_programs(department_code)

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
