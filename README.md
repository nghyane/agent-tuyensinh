# FPT University Agent

AI Agent thông minh cho Đại học FPT với khả năng RAG (Retrieval Augmented Generation) để cung cấp thông tin chính xác và chi tiết về trường đại học.

## 🚀 Tính năng chính

### 🤖 **AI Agent với Agno Framework**
- **Intent Detection**: Phát hiện ý định người dùng thông minh
- **Reasoning Tools**: Suy luận và phân tích logic
- **Memory Management**: Ghi nhớ tương tác người dùng
- **Multi-modal Support**: Hỗ trợ nhiều loại dữ liệu

### 📚 **RAG Knowledge Base**
- **Hybrid Search**: Tìm kiếm kết hợp vector + keyword
- **Vietnamese Optimization**: Tối ưu cho tiếng Việt
- **Reranking**: Cải thiện độ chính xác với Cohere
- **Real-time Updates**: Cập nhật thông tin theo thời gian thực

### 🎓 **FPT University Data**
- **Real-time API**: Dữ liệu trực tiếp từ FPT University API
- **Comprehensive Coverage**: Thông tin đầy đủ về:
  - Học phí các ngành và campus
  - Chương trình đào tạo
  - Thông tin tuyển sinh
  - Chính sách học bổng
  - Thông tin campus

## 🛠️ Cài đặt

### 1. **Clone repository**
```bash
git clone <repository-url>
cd agent
```

### 2. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Cấu hình environment**
```bash
cp env.example .env
```

Chỉnh sửa `.env` file:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/fpt_agent

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Optional: Cohere for reranking
COHERE_API_KEY=your_cohere_api_key
```

### 4. **Setup PostgreSQL với pgvector**
```bash
# Sử dụng Docker
docker run -d \
  -e POSTGRES_DB=fpt_agent \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 5. **Setup RAG Knowledge Base**
```bash
python scripts/setup_rag.py
```

## 🚀 Sử dụng

### **Khởi động API Server**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### **Test Agent với RAG**
```python
import asyncio
from src.api.agents.fpt_agent import create_fpt_agent_manager

async def test_agent():
    async with create_fpt_agent_manager(enable_rag=True) as agent:
        # Test với knowledge base
        response = await agent.run("Chính sách học bổng 2025 như thế nào?")
        print(response)
        
        # Test với API real-time
        response = await agent.run("Học phí ngành CNTT tại campus Hà Nội?")
        print(response)

asyncio.run(test_agent())
```

## 📊 Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  FPT Agent      │───▶│  Response       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Intent Detection│    │ Reasoning Tools │    │ Memory System   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ FPT University  │    │ RAG Knowledge   │    │ Vector Database │
│ API (Real-time) │    │ Base (Reference)│    │ (PgVector)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Cấu hình RAG

### **Knowledge Base Sources**
- `docs/reference/fpt_university_2025_reference.md` - Tài liệu tham khảo chính
- `data/production_rules.json` - Quy tắc sản xuất
- `data/templates.json` - Templates trả lời

### **Search Configuration**
- **Embedder**: OpenAI text-embedding-3-small
- **Search Type**: Hybrid (vector + keyword)
- **Language**: Vietnamese optimized
- **Reranking**: Cohere rerank-multilingual-v3.0 (optional)

### **Performance Optimization**
- **Chunk Size**: 1000 tokens
- **Chunk Overlap**: 200 tokens
- **Vector Score Weight**: 0.7
- **Search Limit**: 5 results (configurable)

## 📈 Monitoring và Logging

### **Agent Performance**
- Tool usage statistics
- Response time metrics
- Memory usage tracking
- Error rate monitoring

### **RAG Performance**
- Search accuracy metrics
- Query response time
- Knowledge base hit rate
- Embedding generation time

## 🔍 Troubleshooting

### **Common Issues**

1. **Knowledge Base không load được**
   ```bash
   # Kiểm tra environment variables
   echo $DATABASE_URL
   echo $OPENAI_API_KEY
   
   # Test setup script
   python scripts/setup_rag.py
   ```

2. **Vector search chậm**
   ```bash
   # Tối ưu PostgreSQL
   ALTER SYSTEM SET shared_preload_libraries = 'vector';
   SELECT pg_reload_conf();
   ```

3. **Memory usage cao**
   ```bash
   # Giảm chunk size
   # Tăng search limit
   # Enable caching
   ```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 🆘 Support

- **Documentation**: [Wiki](link-to-wiki)
- **Issues**: [GitHub Issues](link-to-issues)
- **Discussions**: [GitHub Discussions](link-to-discussions)

---

**FPT University Agent** - AI Assistant thông minh cho Đại học FPT 🎓 