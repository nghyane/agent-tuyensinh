#!/usr/bin/env tsx

import { performance } from 'node:perf_hooks';

interface BenchmarkResult {
  test: string;
  query: string;
  method: string;
  responseTime: number;
  confidence?: number;
  success: boolean;
  metadata?: {
    intent?: string;
    messageCount?: number;
    hasContent?: boolean;
    [key: string]: unknown;
  };
}

interface BenchmarkSuite {
  name: string;
  description: string;
  results: BenchmarkResult[];
  avgResponseTime: number;
  successRate: number;
}

async function runPerformanceBenchmarks() {
  console.log('⚡ Performance Benchmark Suite');
  console.log('='.repeat(70));

  // Test optimized intent detection
  console.log('🎯 Testing Optimized Intent Detection');
  console.log('─'.repeat(70));

  const queries = [
    'Học phí ngành IT FPT bao nhiêu?',
    'Campus Hà Nội có những tiện ích gì?',
    'Thư viện mở cửa lúc mấy giờ?',
    'Điểm chuẩn vào trường năm 2024?',
    'FPT có những ngành nào hot nhất?',
    'OJT có lương không?',
    'Học bổng 100% có thật không?',
    'Hạn nộp hồ sơ khi nào?',
    'AI và Data Science khác nhau thế nào?',
    '98% có việc làm có đúng không?',
  ];

  let _totalTime = 0;
  const results = [];

  for (const query of queries) {
    const { hybridIntentDetectionService } = await import(
      '../../src/services/intent-detection-hybrid.js'
    );

    const startTime = performance.now();
    const intent = await hybridIntentDetectionService.detectIntent(query);
    const endTime = performance.now();

    const responseTime = endTime - startTime;
    _totalTime += responseTime;

    results.push({
      query,
      intent: intent.id,
      confidence: intent.confidence,
      method: intent.method,
      responseTime,
    });

    console.log(`✅ "${query}"`);
    console.log(
      `   Intent: ${intent.id} | Confidence: ${(intent.confidence * 100).toFixed(1)}% | Method: ${intent.method} | Time: ${responseTime.toFixed(0)}ms`
    );
  }

  // Test 2: Agent Response Performance
  console.log('\n🤖 2. Agent Response Performance');
  console.log('─'.repeat(50));

  const agentResults: BenchmarkResult[] = [];
  let totalAgentTime = 0;

  try {
    const { mastra } = await import('../../src/mastra/index.js');

    for (let i = 0; i < Math.min(5, queries.length); i++) {
      const query = queries[i];
      try {
        const startTime = performance.now();
        const agent = mastra.getAgent('admissionsAgent');
        const response = await agent.generate([{ role: 'user', content: query }]);
        const endTime = performance.now();
        const responseTime = endTime - startTime;
        totalAgentTime += responseTime;

        const hasResponse = response.response?.messages?.[0]?.content;
        const result: BenchmarkResult = {
          test: 'agent_response',
          query,
          method: 'Mastra Agent',
          responseTime,
          success: !!hasResponse,
          metadata: {
            messageCount: response.response?.messages?.length || 0,
            hasContent: !!hasResponse,
          },
        };

        agentResults.push(result);

        const status = result.success ? '✅' : '❌';
        console.log(`${status} "${query.substring(0, 35)}..." | ${responseTime.toFixed(0)}ms`);

        // Add delay to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 1000));
      } catch (error) {
        console.log(`❌ "${query.substring(0, 35)}..." | ERROR: ${error}`);
        agentResults.push({
          test: 'agent_response',
          query,
          method: 'Mastra Agent',
          responseTime: 0,
          success: false,
        });
      }
    }
  } catch (_importError) {
    console.log('⚠️  Could not import mastra agent');
    console.log('   This might be due to module path issues or missing dependencies');
  }

  // Test 3: Baseline Regex Performance (for comparison)
  console.log('\n📝 3. Baseline Regex Performance');
  console.log('─'.repeat(50));

  const regexResults: BenchmarkResult[] = [];
  let totalRegexTime = 0;

  for (const query of queries) {
    const startTime = performance.now();

    let intent = 'general_info';
    let confidence = 0.3;

    // Simple regex patterns for baseline comparison
    if (/cơ sở|campus|tiện ích|thư viện/i.test(query)) {
      intent = 'campus_info';
      confidence = 0.6;
    } else if (/học phí|tuition|trả góp|học bổng/i.test(query)) {
      intent = 'tuition_inquiry';
      confidence = 0.7;
    } else if (/ngành|chương trình|program|yêu cầu/i.test(query)) {
      intent = 'program_search';
      confidence = 0.6;
    } else if (/hạn|deadline|nộp hồ sơ/i.test(query)) {
      intent = 'deadline_inquiry';
      confidence = 0.5;
    } else if (/quy trình|xét tuyển|tuyển sinh/i.test(query)) {
      intent = 'admission_process';
      confidence = 0.6;
    }

    const endTime = performance.now();
    const responseTime = endTime - startTime;
    totalRegexTime += responseTime;

    const result: BenchmarkResult = {
      test: 'regex_baseline',
      query,
      method: 'Regex patterns',
      responseTime,
      confidence,
      success: confidence > 0.5,
      metadata: { intent },
    };

    regexResults.push(result);

    const status = result.success ? '✅' : '⚠️';
    console.log(
      `${status} "${query.substring(0, 35)}..." | ${responseTime.toFixed(2)}ms | ${(confidence * 100).toFixed(1)}%`
    );
  }

  // Generate comprehensive benchmark report
  console.log(`\n${'='.repeat(70)}`);
  console.log('📊 COMPREHENSIVE BENCHMARK REPORT');
  console.log('='.repeat(70));

  const suites: BenchmarkSuite[] = [];

  if (agentResults.length > 0) {
    const agentSuccessRate =
      (agentResults.filter((r) => r.success).length / agentResults.length) * 100;
    const avgAgentTime = totalAgentTime / agentResults.length;
    suites.push({
      name: 'Agent Response',
      description: 'End-to-end agent workflow',
      results: agentResults,
      avgResponseTime: avgAgentTime,
      successRate: agentSuccessRate,
    });
  }

  if (regexResults.length > 0) {
    const regexSuccessRate =
      (regexResults.filter((r) => r.success).length / regexResults.length) * 100;
    const avgRegexTime = totalRegexTime / regexResults.length;
    suites.push({
      name: 'Regex Baseline',
      description: 'Pattern matching baseline',
      results: regexResults,
      avgResponseTime: avgRegexTime,
      successRate: regexSuccessRate,
    });
  }

  // Display results
  for (const suite of suites) {
    console.log(`\n🎯 ${suite.name}:`);
    console.log(`   📋 ${suite.description}`);
    console.log(`   ⚡ Avg Response Time: ${suite.avgResponseTime.toFixed(1)}ms`);
    console.log(`   ✅ Success Rate: ${suite.successRate.toFixed(1)}%`);
    console.log(`   📊 Total Tests: ${suite.results.length}`);
  }

  if (suites.length >= 2) {
    console.log('\n📈 Performance Comparison:');
    const agentSuite = suites.find((s) => s.name === 'Agent Response');
    const regexSuite = suites.find((s) => s.name === 'Regex Baseline');

    if (agentSuite && regexSuite) {
      const speedRatio = agentSuite.avgResponseTime / regexSuite.avgResponseTime;
      const accuracyGain = agentSuite.successRate - regexSuite.successRate;

      console.log(`   🚀 Speed: Agent is ${speedRatio.toFixed(1)}x slower than regex`);
      console.log(`   🎯 Accuracy: Agent is +${accuracyGain.toFixed(1)}% more accurate`);
      console.log(
        `   💡 Trade-off: ${speedRatio.toFixed(1)}x time cost for ${accuracyGain.toFixed(1)}% accuracy gain`
      );
    }
  }

  console.log('\n✨ Benchmark Complete!');
  console.log('🔧 Use these metrics to optimize system performance');

  return suites;
}

// Run benchmarks if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runPerformanceBenchmarks()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('💥 Benchmark suite failed:', error);
      process.exit(1);
    });
}

export { runPerformanceBenchmarks };
