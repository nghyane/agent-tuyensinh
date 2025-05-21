import { createTool } from "@mastra/core/tools";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";
import { LibSQLVector } from "@mastra/core/vector/libsql";
import { embed } from "ai";

// Khởi tạo kết nối vector database
const pgVector = new LibSQLVector({
    connectionUrl: "file:./data/mastra.db",
});

export const vectorQueryTool = createTool({
    id: "searchKnowledgeBase",
    description: "Search for information in the school's admissions database",
    inputSchema: z.object({
        query: z.string().describe("Search query"),
        filters: z.object({
            year: z.string().optional().describe("Admission year"),
            documentType: z.string().optional().describe("Document type"),
            language: z.string().optional().describe("Language"),
            campuses: z.array(z.string()).optional().describe("Campus areas"),
            hasEnglishProgram: z.boolean().optional().describe("Has English program"),
            hasInstallmentPolicy: z.boolean().optional().describe("Has installment payment policy")
        }).optional()
    }),
    execute: async ({ context }) => {
        const { embedding } = await embed({
            value: context.query,
            model: openai.embedding('text-embedding-3-small'),
        });


        const filter: Record<string, any> = {};
        if (context.filters) {
            Object.entries(context.filters).forEach(([key, value]) => {
                if (value) filter[key] = value;
            });
        }


        const results = await pgVector.query({
            indexName: "admissions_data",
            queryVector: embedding,
            topK: 5,
            filter: Object.keys(filter).length > 0 ? filter : undefined
        });

        return results;
    }
});
