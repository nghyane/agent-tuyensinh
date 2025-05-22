import { LibSQLVector } from "@mastra/libsql";
import { embed, embedMany } from "ai";
import { openai } from "@ai-sdk/openai";
import { readFile } from "fs/promises";

export type Document = {
    text: string;
    metadata: {
        source: string;
        category: string;
        version: string;
    };
};

const vectorDB = new LibSQLVector({
    connectionUrl: "file:./data/mastra.db",
});

const index = await vectorDB.listIndexes();

if (!index.includes("fpt_university")) {
    vectorDB.deleteIndex({
        indexName: "fpt_university",
    });

    vectorDB.createIndex({
        dimension: 1536,
        indexName: "fpt_university",
    });
}


const chunks = await readFile("./data/chunks.jsonl", "utf-8");

const documents = chunks.split("\n").filter(Boolean).map((chunk) => {
    return JSON.parse(chunk) as Document;
})

// embed documents
const embeddings = await embedMany({
    model: openai.embedding("text-embedding-3-small"),
    values: documents.map((doc) => doc.text),
});

// upsert documents
await vectorDB.upsert({
    indexName: "fpt_university",
    vectors: embeddings.embeddings,
    metadata: documents.map((doc) => doc),
});

console.log("Documents upserted successfully");
