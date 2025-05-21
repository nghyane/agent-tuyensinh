import { LibSQLVector } from "@mastra/core/vector/libsql";
import { embed } from "ai";
import { openai } from "@ai-sdk/openai";



const store = new LibSQLVector({
  connectionUrl: "file:./data/mastra.db",
});

const query = "Campus"

const embeddings = await embed({
  model: openai.embedding("text-embedding-3-small"),
  value: query,
});

const result = await store.query({
  indexName: "fpt_university",
  queryVector: embeddings.embedding,
  topK: 10,
});

console.log(result);
