import { LibSQLVector } from "@mastra/libsql";
import { embed } from "ai";
import { google } from "@ai-sdk/google";

const store = new LibSQLVector({
  connectionUrl: "file:./data/mastra.db",
});

const query = "Campus"

// Use Google text-embedding-004 (768 dimensions)
const embeddings = await embed({
  model: google.textEmbeddingModel("text-embedding-004"),
  value: query,
});

const result = await store.query({
  indexName: "fpt_university",
  queryVector: embeddings.embedding,
  topK: 10,
});

console.log(result);
