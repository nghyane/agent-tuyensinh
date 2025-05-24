# 🧪 Test Suite Documentation

## 📁 Cấu trúc Test được tổ chức (Đã đơn giản hóa)

```
tests/
├── unit/                    # Unit tests - test cốt lõi
│   └── intent-detection-enhanced.test.ts
├── integration/             # Integration tests - test workflow end-to-end  
│   └── agent-workflow.test.ts
├── performance/             # Performance tests - benchmark và optimization
│   └── benchmark.test.ts
├── test-runner.ts          # Test runner chính
└── README.md              # Documentation này
```

## 🚀 Cách chạy Tests

### Chạy tất cả tests (khuyến nghị)
```bash
npm test
# hoặc
pnpm test
```

### Chạy theo loại test
```bash
# Unit tests only
npm run test:unit

# Integration tests only  
npm run test:integration

# Performance tests only
npm run test:performance
```

## 📋 Mô tả các Test Suites

### 🧪 Unit Tests (`tests/unit/`)
- **File**: `intent-detection-enhanced.test.ts`
- **Mục đích**: Test intent detection với các trường hợp cơ bản và edge cases
- **Scope**: Intent classification accuracy, confidence levels, response times
- **Coverage**: Core intents, boundary cases, error handling

### 🔄 Integration Tests (`tests/integration/`)
- **File**: `agent-workflow.test.ts`
- **Mục đích**: Test workflow end-to-end của agent
- **Scope**: Agent response, tool integration, conversation flow
- **Coverage**: Real user queries, agent behavior validation

### ⚡ Performance Tests (`tests/performance/`)
- **File**: `benchmark.test.ts`
- **Mục đích**: Benchmark performance và optimization metrics
- **Scope**: Response times, throughput, method comparison
- **Coverage**: Performance baselines, regression detection

## 🏗️ Lợi ích của cấu trúc đơn giản

### ✅ Tập trung vào cốt lõi
- Chỉ test những tính năng quan trọng nhất
- Giảm thời gian chạy test
- Dễ maintain và debug

### ✅ Hiệu quả cao
- Fast feedback trong development
- Comprehensive coverage với ít test hơn
- Clear failure signals

### ✅ CI/CD friendly
- Nhanh chóng và reliable
- Easy to understand results
- Focused on essential functionality

## 🔧 Cách thêm test mới

### Thêm test case vào Enhanced Unit Test
```typescript
// tests/unit/intent-detection-enhanced.test.ts
// Thêm vào testCases array
{
  description: "Your test description",
  query: "Test query in Vietnamese",
  expectedIntent: "expected_intent_name",
  shouldPass: true,
  minConfidence: 0.7,
  category: "test_category"
}
```

### Cập nhật Integration Test
```typescript
// tests/integration/agent-workflow.test.ts
// Thêm vào testCases array
{
  description: "Integration test scenario",
  query: "User query example",
  expectedWorkflow: "intent_detection → knowledge_search → response",
  shouldContain: ["keyword1", "keyword2"]
}
```

## 📊 Test Coverage Goals

- **Unit Tests**: >85% intent detection accuracy
- **Integration Tests**: >90% workflow success rate  
- **Performance Tests**: <200ms average response time

## 🎯 Best Practices

1. **Focus**: Test only essential functionality
2. **Speed**: Optimize for fast execution
3. **Clarity**: Clear test descriptions and error messages
4. **Coverage**: Ensure all critical paths are tested

## ✨ Đơn giản hóa thành công

Cấu trúc test mới loại bỏ:
- 🗑️ 8 file test trùng lặp và phức tạp không cần thiết
- 🗑️ Test cases quá chi tiết và ít practical value  
- 🗑️ Redundant stress tests và edge cases
- ✅ Giữ lại 3 test suites cốt lõi và hiệu quả 