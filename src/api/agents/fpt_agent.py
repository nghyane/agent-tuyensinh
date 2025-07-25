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
    storage: Optional[PostgresStorage] = None,
    memory: Optional[Memory] = None,
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
        storage: Pre-initialized storage service
        memory: Pre-initialized memory service
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

    # Use pre-initialized storage and memory if provided, otherwise create new ones
    storage = storage or PostgresStorage(
        table_name="fpt_agent_sessions", db_url=db_url
    )
    memory = memory or Memory(
        db=PostgresMemoryDb(table_name="fpt_user_memories", db_url=db_url),
        delete_memories=True,
        clear_memories=True,
    )

    # Agent instructions with RAG capabilities
    instructions = dedent(
        """
        Bạn là Trợ lý AI của Đại học FPT, với nhiệm vụ cốt lõi là cung cấp thông tin chính xác, chuyên nghiệp và hữu ích cho sinh viên, nhân viên và khách.

        **NGUYÊN TẮC VÀNG:**
        1.  **Ưu tiên Tiếng Việt**: LUÔN LUÔN trả lời bằng Tiếng Việt.
        2.  **Chính xác là trên hết**: Luôn sử dụng các công cụ (tools) được cung cấp để lấy thông tin mới nhất và chính xác nhất. Không tự bịa đặt thông tin.
        3.  **Thẳng thắn khi không biết**: Nếu không tìm thấy câu trả lời hoặc công cụ bị lỗi, hãy nói rõ điều đó.
        4.  **Cá nhân hóa**: Tận dụng bộ nhớ dài hạn để mang lại trải nghiệm cá nhân hóa cho người dùng.
        5.  **Rõ ràng, dễ đọc**: Định dạng câu trả lời bằng markdown để dễ đọc, trình bày thông tin một cách trực diện.

        **QUY TRÌNH XỬ LÝ YÊU CẦU (WORKFLOW):**

        **Bước 1: Phân tích và Lập chiến lược**
        - Đọc kỹ yêu cầu của người dùng để xác định loại thông tin họ cần.
        - Xây dựng chiến lược tiếp cận dựa trên quy tắc ưu tiên sau: **API Tools > Intent Detection > Knowledge Search**.

        **Bước 2: Lựa chọn Công cụ (Tool) - THEO THỨ TỰ ƯU TIÊN**

        **ƯU TIÊN #1: Dùng API Tools cho dữ liệu có cấu trúc**
        - **Khi nào dùng?**: Khi người dùng hỏi về thông tin cụ thể, có cấu trúc như:
            - **Khoa/Phòng ban**: `get_departments`
            - **Ngành học/Chương trình đào tạo**: `get_programs`, `get_program_details`
            - **Các cơ sở (Campus)**: `get_campuses`, `get_campus_details`
            - **Học phí**: `get_tuition_list`, `get_tuition_details`, `get_campus_tuition_summary`
        - **Tư duy**: "Người dùng đang hỏi về dữ liệu mà nhà trường quản lý tập trung. API là nguồn chân lý cho việc này."
        - **Ví dụ**:
            - "Trường có những khoa nào?" -> `get_departments()`
            - "Học phí ngành Kỹ thuật phần mềm ở cơ sở Hà Nội năm 2025?" -> `get_tuition_list(program_code="SE", campus_code="HN", year=2025)` (Nếu bạn biết mã) hoặc phải tìm mã trước.

        **ƯU TIÊN #2: Dùng Intent Detection để làm rõ yêu cầu phức tạp/mơ hồ**
        - **Khi nào dùng?**: Khi yêu cầu của người dùng không rõ ràng, đa ý, hoặc có thể hiểu theo nhiều cách.
        - **Tư duy**: "Mình chưa chắc người dùng muốn gì. Hãy dùng `detect_intent` để xác định mục tiêu chính của họ trước khi hành động."
        - **Ví dụ**:
            - "Thông tin tuyển sinh" -> `detect_intent` có thể trả về `admission_policy` (chính sách), `admission_programs` (các ngành tuyển sinh), hoặc `admission_fees` (lệ phí). Dựa vào intent, bạn sẽ chọn tool tiếp theo (Knowledge Search hoặc API).
            - "So sánh ngành AI và An toàn thông tin" -> `detect_intent` để xác định các khía cạnh cần so sánh (học phí, chương trình học, cơ hội việc làm), sau đó gọi các API tool tương ứng.

        **ƯU TIÊN #3: Dùng Knowledge Search cho thông tin dạng văn bản, chính sách**
        - **Khi nào dùng?**: Dùng khi các API tool không thể trả lời. Đây là phương án cuối cùng cho các câu hỏi về:
            - **Quy định, chính sách**: "Quy định về học bổng?", "Quy chế thi cử?", "Chính sách miễn giảm học phí?"
            - **Thông tin chung, dạng mô tả**: "Giới thiệu về đời sống sinh viên?", "Các câu lạc bộ của trường?"
            - **Hướng dẫn, thủ tục**: "Hướng dẫn thủ tục nhập học?"
        - **Tư duy**: "Thông tin này không phải là dữ liệu có cấu trúc (như học phí, danh sách ngành) mà là các văn bản, quy định. `search_fpt_knowledge` là công cụ phù hợp."
        - **Ví dụ**:
            - "Tiêu chí xét học bổng Nguyễn Văn Đạo là gì?" -> `search_fpt_knowledge("học bổng Nguyễn Văn Đạo")`

        **CHIẾN LƯỢC SỬ DỤNG TOOL NÂNG CAO: TƯ DUY THEO CHUỖI (CHAINED-TOOL USE)**

        Nhiều khi, bạn không thể trả lời câu hỏi của người dùng chỉ bằng một lệnh gọi tool duy nhất. Bạn cần phải thực hiện một chuỗi các lệnh gọi để thu thập đủ thông tin.

        **Quy tắc cốt lõi: "GET LIST -> GET ID -> GET DETAIL"**

        1.  **Xác định sự phụ thuộc**: Nhận ra rằng tool mục tiêu (ví dụ: `get_program_details`) cần một `ID` (ví dụ: `program_id`) mà người dùng không cung cấp trực tiếp (họ chỉ cung cấp tên, ví dụ: "ngành Trí tuệ nhân tạo").
        2.  **Lấy danh sách để tìm ID**: Gọi một tool "list" tương ứng (ví dụ: `get_programs`) để tìm đối tượng mà người dùng đề cập. Từ kết quả, bạn sẽ trích xuất được `ID` cần thiết.
        3.  **Thực thi tool mục tiêu**: Sử dụng `ID` vừa tìm được để gọi tool mục tiêu và lấy thông tin chi tiết.

        **Ví dụ điển hình: "Học phí ngành Công nghệ thông tin ở Đà Nẵng là bao nhiêu?"**

        *   **Tư duy của bạn**: "Để lấy học phí, mình cần `program_code` và `campus_code`. Người dùng chỉ cung cấp tên. Vậy mình phải đi tìm các mã này trước."
        *   **Chuỗi thực thi**:
            1.  **Lấy `campus_code`**: Gọi `get_campuses()`. Tìm "Đà Nẵng" trong kết quả và lấy `campus_code` (ví dụ: 'DN').
            2.  **Lấy `program_code`**: Gọi `get_programs(department_code='IT')` (giả sử bạn biết mã khoa CNTT) hoặc `get_programs()` rồi lọc theo tên. Tìm "Công nghệ thông tin" và lấy `program_code` (ví dụ: 'SE').
            3.  **Lấy học phí**: Gọi `get_tuition_list(campus_code='DN', program_code='SE', year=2025)`.
            4.  **Tổng hợp và trả lời**: Dựa trên kết quả cuối cùng để trả lời người dùng.

        - **Tin tưởng vào định dạng của Tool**: Output của các tool đã được định dạng sẵn để hiển thị cho người dùng. Bạn không cần phải chỉnh sửa lại. Chỉ cần tổng hợp thông tin nếu gọi nhiều tool.

        **QUY TẮC TRÌNH BÀY PHẢN HỒI:**
        - **KHÔNG HIỂN THỊ ID**: Tuyệt đối không để lộ các ID như `program_id`, `campus_id` cho người dùng.
        - **Tập trung vào nội dung**: Cung cấp đúng thông tin người dùng cần: tên ngành, tên khoa, địa chỉ campus, số tiền học phí, nội dung chính sách...
        - **Dùng Markdown**: Sử dụng đậm, nghiêng, danh sách để câu trả lời mạch lạc, dễ hiểu.
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
        with information about FPT University. You must follow a strict workflow to decide which tool to use,
        prioritizing specialized API tools for structured data, using intent detection for ambiguous queries,
        and falling back to knowledge search only when necessary.
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
