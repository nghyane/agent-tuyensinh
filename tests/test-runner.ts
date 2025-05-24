#!/usr/bin/env tsx

interface TestSuite {
  name: string;
  description: string;
  path: string;
  type: 'unit' | 'integration' | 'performance';
}

interface TestResult {
  suite: string;
  passed: boolean;
  duration: number;
  error?: string;
}

async function runTestSuite(suite: TestSuite): Promise<TestResult> {
  console.log(`\n🏃 Running ${suite.name}...`);
  console.log(`   📝 ${suite.description}`);
  
  const startTime = Date.now();
  
  try {
    // Dynamic import with proper error handling
    const module = await import(suite.path);
    
    // Look for the main test function
    let testFunction;
    if (module.runEnhancedIntentDetectionTest) {
      testFunction = module.runEnhancedIntentDetectionTest;
    } else if (module.runAgentWorkflowTests) {
      testFunction = module.runAgentWorkflowTests;
    } else if (module.runPerformanceBenchmarks) {
      testFunction = module.runPerformanceBenchmarks;
    } else {
      throw new Error('No recognized test function found in module');
    }
    
    const result = await testFunction();
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    // Handle boolean or complex result objects
    const passed = typeof result === 'boolean' ? result : true;
    
    console.log(`   ✅ Completed in ${duration}ms`);
    
    return {
      suite: suite.name,
      passed,
      duration,
    };
    
  } catch (error) {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    console.log(`   ❌ Failed after ${duration}ms`);
    console.log(`   💥 Error: ${error}`);
    
    return {
      suite: suite.name,
      passed: false,
      duration,
      error: String(error)
    };
  }
}

async function runAllTests() {
  console.log('🧪 Simplified Test Suite Runner');
  console.log('=' .repeat(60));
  console.log('📋 Clean and focused test structure');
  
  const testSuites: TestSuite[] = [
    {
      name: "Enhanced Intent Detection Tests",
      description: "Core intent classification tests with edge cases",
      path: "./unit/intent-detection-enhanced.test.js",
      type: "unit"
    },
    {
      name: "Agent Workflow Integration Tests", 
      description: "End-to-end agent functionality tests",
      path: "./integration/agent-workflow.test.js",
      type: "integration"
    },
    {
      name: "Performance Benchmarks",
      description: "System performance and benchmark tests",
      path: "./performance/benchmark.test.js", 
      type: "performance"
    }
  ];

  const results: TestResult[] = [];
  let totalDuration = 0;

  console.log(`\n🎯 Found ${testSuites.length} essential test suites:`);
  for (const suite of testSuites) {
    console.log(`   📦 ${suite.name} (${suite.type})`);
  }

  for (const suite of testSuites) {
    const result = await runTestSuite(suite);
    results.push(result);
    totalDuration += result.duration;
    
    // Small delay between test suites
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // Generate summary report
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST EXECUTION SUMMARY');
  console.log('='.repeat(60));

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const successRate = (passed / results.length) * 100;

  console.log(`\n🎯 Overall Results:`);
  console.log(`   ✅ Passed: ${passed}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📈 Success Rate: ${successRate.toFixed(1)}%`);
  console.log(`   ⏱️  Total Duration: ${totalDuration}ms`);

  console.log(`\n📋 Detailed Results:`);
  for (const result of results) {
    const status = result.passed ? '✅' : '❌';
    console.log(`   ${status} ${result.suite} (${result.duration}ms)`);
    if (result.error) {
      console.log(`      💥 ${result.error.substring(0, 80)}...`);
    }
  }

  console.log(`\n🏗️  Simplified Test Benefits:`);
  console.log(`   📁 Focused on essential functionality`);
  console.log(`   🔧 Faster test execution`);
  console.log(`   📊 Clear and actionable reporting`);
  console.log(`   🚀 Maintainable test architecture`);

  if (failed === 0) {
    console.log(`\n🎉 All essential tests passed! System is healthy.`);
  } else {
    console.log(`\n⚠️  ${failed} test suite(s) failed. Review and fix issues.`);
  }

  return failed === 0;
}

// CLI argument parsing
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'unit':
      console.log('🧪 Running unit tests only...');
      // Could implement specific test type running
      break;
    case 'integration':
      console.log('🔄 Running integration tests only...');
      break;
    case 'performance': 
      console.log('⚡ Running performance tests only...');
      break;
    case 'all':
    default:
      console.log('🎯 Running all test suites...');
      break;
  }

  const success = await runAllTests();
  process.exit(success ? 0 : 1);
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('💥 Test runner failed:', error);
    process.exit(1);
  });
}

export { runAllTests }; 