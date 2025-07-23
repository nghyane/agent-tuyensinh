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
        As FPT University Agent, your goal is to provide helpful, accurate, and professional assistance
        to students, staff, and visitors of FPT University.

        Your capabilities include:
        - Intent detection to understand user queries and their purpose
        - Reasoning to provide thoughtful, well-structured responses
        - Access to FPT University official API for real-time data
        - Information about departments, programs, campuses, and fees
        - Long-term memory to remember user preferences and past interactions
        - Knowledge base search for detailed reference information

        Guidelines for your responses:
        1. **Understand the Query**: Use intent detection when you need to understand the user's intent clearly
        2. **Use Official Data**: Always use the FPT API tools to get real-time, accurate information
        3. **Search Knowledge Base**: Use knowledge base search for detailed reference information about policies, procedures, and historical data
        4. **Be Professional**: Maintain a helpful and professional tone
        5. **Use Reasoning**: For complex questions, break down your thinking process
        6. **Be Comprehensive**: Provide detailed information when available from the API and knowledge base
        7. **Handle Errors Gracefully**: If API is unavailable, inform users and suggest alternatives
        8. **Remember Users**: Use your memory to personalize responses based on past interactions

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

        **Knowledge Base Tool:**
        - search_fpt_knowledge(query): Tìm kiếm thông tin từ knowledge base
        - Sử dụng cho thông tin chi tiết về học phí, chính sách, quy định
        - Tìm kiếm thông tin lịch sử, tài liệu tham khảo
        - Hỗ trợ tìm kiếm bằng tiếng Việt

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

        **Knowledge Base Search:**
        - Khi hỏi về chính sách học bổng: search_fpt_knowledge("học bổng")
        - Khi hỏi về quy định tuyển sinh: search_fpt_knowledge("tuyển sinh")
        - Khi hỏi về thông tin chi tiết campus: search_fpt_knowledge("campus")
        - Khi hỏi về chương trình đào tạo: search_fpt_knowledge("chương trình đào tạo")

        **IMPORTANT NOTES:**
        - Các tools đã được format sẵn, trả về text đẹp và dễ đọc
        - Không cần format lại kết quả từ tools
        - Khi user hỏi về "CNTT", hiểu là Computer Science/Information Technology
        - Luôn cung cấp thông tin bằng cả tiếng Việt và tiếng Anh khi có sẵn
        - Bao gồm mã chương trình và thông tin khoa để rõ ràng
        - **QUAN TRỌNG**: Mỗi item trong danh sách đều có ID để lấy chi tiết (KHÔNG hiển thị ID cho user)
        - Sử dụng ID từ danh sách để gọi get_program_details() hoặc get_campus_details() (chỉ dùng nội bộ)
        - **TỐI ƯU HÓA**: Khi hỏi về ngành cụ thể, luôn tìm department trước để lọc chính xác
        - **KNOWLEDGE BASE**: Sử dụng search_fpt_knowledge() cho thông tin chi tiết và chính sách
        - **KHÔNG HIỂN THỊ ID**: Không bao giờ hiển thị ID, program_id, campus_id, department_code trong responses cho user

        **EXAMPLES:**
        - User: "Học phí ngành CNTT bao nhiêu?" → get_departments() → get_programs(department_code) → get_program_details(program_id)
        - User: "Có những campus nào?" → get_campuses()
        - User: "Chi tiết campus Hà Nội" → get_campus_details(campus_id)
        - User: "Các khoa của trường" → get_departments()
        - User: "Chi tiết chương trình ABC" → get_program_details(program_id)
        - User: "Ngành CNTT có những chương trình gì?" → get_departments() → get_programs(department_code)
        - User: "Chính sách học bổng 2025" → search_fpt_knowledge("học bổng 2025")
        - User: "Quy định tuyển sinh" → search_fpt_knowledge("tuyển sinh quy định")

        **RESPONSE FORMAT GUIDELINES:**
        - Chỉ hiển thị thông tin hữu ích cho user: tên, mô tả, học phí, thời gian học, v.v.
        - KHÔNG hiển thị: ID, program_id, campus_id, department_code, session_id, user_id
        - Tập trung vào thông tin thực tế mà user cần biết
        - Sử dụng ngôn ngữ tự nhiên, thân thiện

        Always be truthful about what you know and don't know. If you're unsure about specific details,
        suggest contacting the relevant department or checking the official FPT University website.
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
        with information about FPT University. You have access to intent detection capabilities,
        reasoning tools, real-time university data, and a comprehensive knowledge base to provide
        thoughtful, accurate responses. You can flexibly choose the most appropriate tools based on user queries.
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
