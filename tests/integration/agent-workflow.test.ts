#!/usr/bin/env tsx

import { mastra } from "../../src/mastra/index.js";

interface WorkflowTestCase {
  description: string;
  query: string;
  expectedWorkflow: string;
  shouldContain: string[];
}

async function runAgentWorkflowTests() {
  console.log('🔄 Agent Workflow Integration Tests');
  console.log('─'.repeat(60));

  const testCases: WorkflowTestCase[] = [
    {
      description: "Campus information workflow",
      query: "Cơ sở Hà Nội có những tiện ích gì?",
      expectedWorkflow: "intent_detection → knowledge_search → response",
      shouldContain: ["cơ sở", "Hà Nội", "tiện ích"]
    },
    {
      description: "Tuition inquiry workflow", 
      query: "Học phí ngành CNTT năm 2024 bao nhiêu?",
      expectedWorkflow: "intent_detection → knowledge_search → response",
      shouldContain: ["học phí", "CNTT", "2024"]
    },
    {
      description: "Program search workflow",
      query: "Trường có những ngành nào?",
      expectedWorkflow: "intent_detection → knowledge_search → response", 
      shouldContain: ["ngành", "chương trình"]
    },
    {
      description: "General admission workflow",
      query: "Quy trình xét tuyển như thế nào?",
      expectedWorkflow: "intent_detection → knowledge_search → response",
      shouldContain: ["quy trình", "xét tuyển"]
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const testCase of testCases) {
    try {
      console.log(`\n🎯 Test: ${testCase.description}`);
      console.log(`   Query: "${testCase.query}"`);
      console.log(`   Expected workflow: ${testCase.expectedWorkflow}`);
      
      const startTime = Date.now();
      
      const agent = mastra.getAgent("admissionsAgent");
      const response = await agent.generate([
        { role: 'user', content: testCase.query }
      ]);

      const endTime = Date.now();
      const responseTime = endTime - startTime;

      if (response.response?.messages?.[0]) {
        const message = response.response.messages[0];
        const hasContent = message.content && typeof message.content === 'string';
        
        // Check if response contains expected keywords (case-insensitive)
        let containsKeywords = true;
        if (hasContent) {
          const content = message.content.toString().toLowerCase();
          containsKeywords = testCase.shouldContain.some(keyword => 
            content.includes(keyword.toLowerCase())
          );
        }

        if (hasContent && (containsKeywords || testCase.shouldContain.length === 0)) {
          console.log(`   ✅ PASS (${responseTime}ms)`);
          console.log(`      Response type: ${message.role}`);
          console.log(`      Has content: ${hasContent}`);
          console.log(`      Keywords found: ${containsKeywords}`);
          passed++;
        } else {
          console.log(`   ❌ FAIL (${responseTime}ms)`);
          console.log(`      Has content: ${hasContent}`);
          console.log(`      Keywords found: ${containsKeywords}`);
          console.log(`      Expected keywords: ${testCase.shouldContain.join(', ')}`);
          failed++;
        }
      } else {
        console.log(`   ❌ FAIL (${responseTime}ms)`);
        console.log(`      No response messages found`);
        failed++;
      }

      // Add delay between requests to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1500));
      
    } catch (error) {
      console.log(`   💥 ERROR: ${error}`);
      failed++;
    }
  }

  console.log('\n' + '─'.repeat(60));
  console.log('📊 Integration Test Results:');
  console.log(`   ✅ Passed: ${passed}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);
  
  if (failed === 0) {
    console.log('\n🎉 All integration tests passed!');
    console.log('✨ Agent workflow is functioning correctly');
  } else {
    console.log('\n⚠️  Some integration tests failed.');
    console.log('🔧 Check agent configuration and tool integrations.');
  }
  
  return failed === 0;
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAgentWorkflowTests()
    .then((success) => process.exit(success ? 0 : 1))
    .catch((error) => {
      console.error('💥 Integration test suite failed:', error);
      process.exit(1);
    });
}

export { runAgentWorkflowTests }; 