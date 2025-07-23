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


async def demo_batch_processing():
    """Demo batch processing với multiple queries"""
    
    print("🚀 Demo Batch Processing - FPT University Agent...")
    
    # Khởi tạo service factory
    service_factory = ServiceFactory()
    
    # Khởi tạo services
    success = await service_factory.initialize_services(
        model_id="gpt-4o",
        debug_mode=False
    )
    
    if not success:
        print("❌ Không thể khởi tạo services")
        return
    
    # Lấy intent detection service
    intent_service = service_factory.get_intent_service()
    if not intent_service:
        print("❌ Không thể lấy intent service")
        return
    
    # Danh sách câu hỏi test cho batch processing
    test_queries = [
        "Học phí ngành CNTT là bao nhiêu?",
        "Điều kiện tuyển sinh vào FPT University?",
        "Campus Hà Nội có những ngành nào?",
        "Thời gian đăng ký học kỳ mới?",
        "Học bổng cho sinh viên giỏi?",
        "Thực tập tại FPT có lương không?",
        "Cách liên hệ phòng đào tạo?",
        "Ngành AI có khó không?",
        "Ký túc xá FPT như thế nào?",
        "Tốt nghiệp có việc làm ngay không?"
    ]
    
    print(f"\n📝 Sẽ xử lý {len(test_queries)} câu hỏi đồng thời...")
    print("=" * 60)
    
    # Đo thời gian xử lý batch
    start_time = asyncio.get_event_loop().time()
    
    # Xử lý batch với max_concurrent=5
    results = await intent_service.detect_batch_queries(
        queries=test_queries,
        max_concurrent=5
    )
    
    end_time = asyncio.get_event_loop().time()
    batch_time = (end_time - start_time) * 1000
    
    print(f"\n✅ Batch processing hoàn thành trong {batch_time:.1f}ms")
    print(f"📊 Trung bình {batch_time/len(test_queries):.1f}ms/query")
    print("=" * 60)
    
    # Hiển thị kết quả
    for i, (query, result) in enumerate(zip(test_queries, results), 1):
        confidence_emoji = "🟢" if result.confidence >= 0.7 else "🟡" if result.confidence >= 0.5 else "🔴"
        print(f"\n{i:2d}. {query}")
        print(f"    {confidence_emoji} Intent: {result.id}")
        print(f"    📊 Confidence: {result.confidence:.3f}")
        print(f"    🔧 Method: {result.method.value}")
    
    print(f"\n🎯 Tổng kết:")
    high_conf = sum(1 for r in results if r.confidence >= 0.7)
    medium_conf = sum(1 for r in results if 0.5 <= r.confidence < 0.7)
    low_conf = sum(1 for r in results if r.confidence < 0.5)
    
    print(f"   🟢 High confidence (≥0.7): {high_conf}")
    print(f"   🟡 Medium confidence (0.5-0.7): {medium_conf}")
    print(f"   🔴 Low confidence (<0.5): {low_conf}")
    
    # So sánh với xử lý tuần tự
    print(f"\n⚡ So sánh hiệu suất:")
    print(f"   Batch processing: {batch_time:.1f}ms")
    
    # Ước tính thời gian xử lý tuần tự (giả sử mỗi query mất ~200ms)
    estimated_sequential = len(test_queries) * 200
    print(f"   Sequential (ước tính): {estimated_sequential:.1f}ms")
    print(f"   Tăng tốc: {estimated_sequential/batch_time:.1f}x")

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
        # "Chính sách học bổng 2025 của FPT có gì mới?"
        "Điểm chuẩn ngành AI năm 2025?",
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
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        print("🚀 Running Batch Processing Demo...")
        asyncio.run(demo_batch_processing())
    else:
        print("🚀 Running Standard Demo...")
        print("💡 Use 'python demo.py batch' for batch processing demo")
        asyncio.run(main())
