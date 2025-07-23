#!/usr/bin/env python3
"""
Demo script để chạy FPT University Agent trực tiếp
Sử dụng service_factory để khởi tạo agent
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from api.factories.service_factory import ServiceFactory
from api.agents.fpt_agent import create_fpt_agent_manager


async def main():
    """Main function để chạy agent demo với list câu hỏi có sẵn"""

    print("🚀 Khởi tạo FPT University Agent...")

    # Khởi tạo service factory
    service_factory = ServiceFactory()

    # Khởi tạo services
    await service_factory.initialize_services(
        model_id="gpt-4o",
        debug_mode=False
    )

    # Lấy intent service
    intent_service = service_factory.get_intent_service()

    # List câu hỏi demo
    demo_questions = [
        # "Học phí ngành CNTT bao nhiêu?",
        "Chính sách học bổng 2025 của FPT có gì mới?"
        # "Điểm chuẩn ngành AI năm 2025?",
        # "Cơ sở FPT ở đâu?",
        # "Thời gian học ngành Software Engineering?",
        # "Có chương trình học bổng không?",
        # "Thư viện mở cửa giờ nào?",
        # "Có ký túc xá cho sinh viên không?",
        # "Ngành Data Science học những gì?",
        # "Có chương trình trao đổi sinh viên không?",
        # "Thời tiết hôm nay thế nào?"
    ]

    # Sử dụng context manager để đảm bảo cleanup
    async with create_fpt_agent_manager(intent_service=intent_service) as agent:
        print("✅ Agent đã sẵn sàng!")
        print("=" * 50)

        # Chạy demo với list câu hỏi
        for i, question in enumerate(demo_questions, 1):
            print(f"\n🔍 Câu hỏi {i}: {question}")

            # Chạy agent
            await agent.aprint_response(question, user_id="demo_user", stream=True)

            print("-" * 50)

        print("\n✅ Demo hoàn thành!")


if __name__ == "__main__":
    asyncio.run(main())
