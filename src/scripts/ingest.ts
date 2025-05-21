import { MDocument } from "@mastra/rag";
import { execFile } from 'child_process';
import { promisify } from 'util';
import { readdir, writeFile } from "fs/promises";
import { createWriteStream } from "fs";
import { extname } from "path";
import { mastra } from "@/mastra/index";

const execFileAsync = promisify(execFile);

const SUPPORTED_EXTENSIONS = [
   ".docx", ".pptx", ".xlsx",
   ".odt", ".odp", ".ods", ".pdf",
   ".html", ".htm", ".epub", ".md"
 ];

/**
 * Parse document using Pandoc to convert to Markdown format
 * @param filePath Path to the document file
 * @returns Markdown text content
 */
async function parseWithPandoc(filePath: string): Promise<string> {
  try {
    // Use different Pandoc options based on file extension
    const ext = extname(filePath).toLowerCase();
    const pandocArgs = [
      filePath,
      '-t', 'markdown',
      '--wrap=none',  // No automatic line wrapping
      '--extract-media=./data/media' // Extract embedded images
    ];
    
    // Add specific options for PDF files
    if (ext === '.pdf') {
      pandocArgs.push('--pdf-engine=xelatex');
    }
    
    const { stdout } = await execFileAsync('pandoc', pandocArgs);
    return stdout;
  } catch (error: unknown) {
    console.error('Pandoc conversion error:', error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to convert document with Pandoc: ${errorMessage}`);
  }
}

function parseGeminiPartsJson<T = any>(parts: any): T {
  const textPart = parts.find((p: any) => p.type === 'text');
  if (!textPart || typeof textPart.text !== 'string') {
    throw new Error("No text part found");
  }

  const cleaned = textPart.text
    .replace(/^```json/, '')
    .replace(/^```/, '')
    .replace(/```$/, '')
    .trim();

  return JSON.parse(cleaned);
}

/**
 * Ingest all .docx files in the data directory, chunk and save as JSONL.
 */
export async function ingestAllDocs(dataDir = "./data", jsonlPath = "./data/chunks.jsonl") {
  const files = await readdir(dataDir);
  const officeFiles = files.filter((f) => SUPPORTED_EXTENSIONS.includes(extname(f)));

  const writer = createWriteStream(jsonlPath);

  for (const file of officeFiles) {
    try {
      const filePath = `${dataDir}/${file}`;
      const officeDocument = await parseWithPandoc(filePath);

      const metadataAgent = mastra.getAgent("metadataAgent");
      const metadata = await metadataAgent.generate(officeDocument).catch((err) => {
        console.error(`[ERROR] Failed to ingest ${file}:`, err);
        return null;
      });

      if (!metadata) {
        continue;
      }


      const document = MDocument.fromMarkdown(officeDocument, {
        source: file,
        category: "office_document",
        ...parseGeminiPartsJson(metadata.response.messages[0].content)
      });

      const chunks = await document.chunk({
        strategy: "markdown",
      });

      for (const chunk of chunks) {
        writer.write(JSON.stringify(chunk) + "\n");
      }

      console.log(`[SUCCESS] Ingested: ${file} (${chunks.length} chunks)`);
    } catch (err) {
      console.error(`[ERROR] Failed to ingest ${file}:`, err);
    }
  }

  writer.end();
}

await ingestAllDocs();