#!/usr/bin/env tsx

import { google } from "@ai-sdk/google";
import { embedMany } from "ai";
import { LibSQLVector } from "@mastra/libsql";
import fs from "fs/promises";
import path from "path";

interface IntentExample {
  id: string;
  category: string;
  routing: string;
  tools: string[];
  examples: string[];
}

interface Document {
  id: string;
  content: string;
  metadata: {
    intentId: string;
    category: string;
    routing: string;
    tools: string[];
  };
}

// Helper function to chunk array into smaller batches
function chunkArray<T>(array: T[], chunkSize: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
}

async function indexIntentExamples() {
  console.log('🚀 Starting intent examples indexing...');
  const startTime = Date.now();

  try {
    // Initialize vector database
    const vectorDB = new LibSQLVector({
      connectionUrl: "file:./data/mastra.db",
    });

    // Create/recreate index
    try {
      await vectorDB.deleteIndex({ indexName: "intent_examples" });
    } catch {
      // Index doesn't exist, continue
    }
    
    await vectorDB.createIndex({
      indexName: "intent_examples",
      dimension: 768,
      metric: "cosine"
    });

    // Load and prepare data
    const filePath = path.join(process.cwd(), 'data', 'intent-examples.json');
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const data = JSON.parse(fileContent);
    const intentExamples: IntentExample[] = data.intents;

    // Prepare documents
    const documents: Document[] = [];
    for (const intent of intentExamples) {
      for (let exampleIndex = 0; exampleIndex < intent.examples.length; exampleIndex++) {
        documents.push({
          id: `intent_${intent.id}_example_${exampleIndex}`,
          content: intent.examples[exampleIndex],
          metadata: {
            intentId: intent.id,
            category: intent.category,
            routing: intent.routing,
            tools: intent.tools
          }
        });
      }
    }

    console.log(`📄 Processing ${documents.length} examples from ${intentExamples.length} categories`);

    // Create embeddings in batches
    const BATCH_SIZE = 100;
    const documentChunks = chunkArray(documents, BATCH_SIZE);
    const allEmbeddings: number[][] = [];

    for (let i = 0; i < documentChunks.length; i++) {
      const chunk = documentChunks[i];
      const embeddingResult = await embedMany({
        model: google.textEmbeddingModel('text-embedding-004'),
        values: chunk.map(doc => doc.content),
      });
      allEmbeddings.push(...embeddingResult.embeddings);
      console.log(`⚡ Batch ${i + 1}/${documentChunks.length} completed`);
    }

    // Bulk upsert all vectors
    await vectorDB.upsert({
      indexName: "intent_examples",
      vectors: allEmbeddings,
      metadata: documents.map(doc => doc.metadata),
      ids: documents.map(doc => doc.id)
    });

    // Verify indexing
    const testResult = await vectorDB.query({
      indexName: "intent_examples", 
      queryVector: allEmbeddings[0],
      topK: 1
    });

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    console.log('✅ Intent indexing completed successfully!');
    console.log(`📊 ${allEmbeddings.length} examples indexed in ${duration.toFixed(2)}s`);
    console.log(`🔍 Verification: ${testResult.length > 0 ? 'PASSED' : 'FAILED'}`);

  } catch (error) {
    console.error('💥 Intent indexing failed:', error);
    process.exit(1);
  }
}

// Run the script
if (import.meta.url === `file://${process.argv[1]}`) {
  indexIntentExamples()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('💥 Script failed:', error);
      process.exit(1);
    });
} 