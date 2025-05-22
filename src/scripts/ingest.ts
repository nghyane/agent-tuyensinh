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

function parseGeminiPartsJson<T = any>(parts: any): T | null {
  if (!Array.isArray(parts)) {
    console.error("Invalid metadata parts: not an array", parts);
    return null;
  }
  const textPart = parts.find((p: any) => p && typeof p === 'object' && p.type === 'text');
  if (!textPart || typeof textPart.text !== 'string') {
    console.error("No valid text part found in metadata parts:", parts);
    return null;
  }

  const cleaned = textPart.text
    .replace(/^```json/, '')
    .replace(/^```/, '')
    .replace(/```$/, '')
    .trim();

  if (!cleaned) {
    console.error("Cleaned text part is empty after removing markdown fences.");
    return null;
  }

  try {
    return JSON.parse(cleaned);
  } catch (error) {
    console.error("Failed to parse JSON from cleaned text part:", cleaned, error);
    return null;
  }
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
        console.error(`[ERROR] Failed to ingest ${file}: Could not generate metadata.`, err);
        return null;
      });

      if (!metadata || !metadata.response || !Array.isArray(metadata.response.messages) || metadata.response.messages.length === 0) {
        console.error(`[ERROR] Failed to ingest ${file}: Invalid or empty metadata response.`);
        continue;
      }
      
      const parsedMetadata = parseGeminiPartsJson(metadata.response.messages[0].content);

      if (!parsedMetadata) {
        console.error(`[ERROR] Failed to ingest ${file}: Could not parse metadata JSON.`);
        continue;
      }


      const document = MDocument.fromMarkdown(officeDocument, {
        source: file,
        category: "office_document",
        ...parsedMetadata
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