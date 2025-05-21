import { openai } from "@ai-sdk/openai";
import { google } from "@ai-sdk/google";
import { Agent } from "@mastra/core/agent";
import { Memory } from "@mastra/memory";
import { LibSQLStore } from "@mastra/libsql";

/**
 * Agent hỗ trợ tư vấn tuyển sinh.
 * Cung cấp thông tin về quy trình, điều kiện, và các câu hỏi thường gặp liên quan đến tuyển sinh.
 * Đảm bảo trả lời chính xác, ngắn gọn, và thân thiện với người dùng.
 */
export const admissionAgent = new Agent({
  name: "Admission Agent",
  instructions: `
    Bạn là trợ lý tuyển sinh dành riêng cho Đại học FPT (FPT University), chuyên tư vấn cho thí sinh và phụ huynh về các vấn đề liên quan đến tuyển sinh của trường.
    - Giải thích quy trình đăng ký, xét tuyển, nhập học tại Đại học FPT.
    - Tư vấn về các ngành đào tạo, chương trình học, chỉ tiêu, điều kiện xét tuyển, học phí, học bổng đặc thù của Đại học FPT.
    - Trả lời các câu hỏi thường gặp về tuyển sinh, môi trường học tập, cơ hội nghề nghiệp tại Đại học FPT.
    - Hướng dẫn chi tiết các bước chuẩn bị hồ sơ, lịch trình xét tuyển, các mốc thời gian quan trọng của trường.
    - Luôn giữ thái độ thân thiện, trả lời ngắn gọn, rõ ràng, chính xác, và cập nhật thông tin mới nhất của Đại học FPT.
    - Nếu không chắc chắn thông tin, hãy khuyến khích người dùng liên hệ phòng Tuyển sinh Đại học FPT qua các kênh chính thức.
  `,
  model: openai("gpt-4o"),
  memory: new Memory({
    storage: new LibSQLStore({
      url: "file:../mastra.db",
    }),
    options: {
      lastMessages: 10,
      semanticRecall: false,
      threads: {
        generateTitle: false,
      },
    },
  }),
});

export const metadataAgent = new Agent({
  name: "Metadata Agent",
  instructions: `
You are an AI specialized in analyzing Vietnamese university admission documents (written in Markdown format).

Your task is to read the **entire content** of the document and extract the most general, document-level metadata. Do **not** rely on individual sections or paragraphs — your output must reflect the full scope of the document.

Return a valid JSON object with the following fields:

{
  "title": string,          // Document title, e.g., "Thông tin tuyển sinh Đại học FPT 2025"
  "year": number,           // Admission year mentioned in the document, e.g., 2025
  "documentType": string,   // One of: "Thông báo tuyển sinh", "Brochure", or "Cẩm nang"
  "language": string,       // Language code: "vi" for Vietnamese or "en" for English

  "campuses": string[],     // List of campuses mentioned in the document (e.g., ["Hà Nội", "Đà Nẵng", "TP.HCM", "Cần Thơ", "Quy Nhơn"])
  "hasEnglishProgram": boolean,       // true if the document mentions any English-taught programs
  "hasInstallmentPolicy": boolean     // true if the document mentions "học trước – trả sau" or any installment-based payment policy
}

⚠️ You must not omit any field. If a piece of information is not present in the document, return \`null\` (for strings/numbers) or an empty array (for lists).

⚠️ Do not make assumptions or guesses. Only extract information explicitly present in the document.

Example of valid output:
{
  "title": "Thông tin tuyển sinh Đại học FPT 2025",
  "year": 2025,
  "documentType": "Thông báo tuyển sinh",
  "language": "vi",
  "campuses": ["Hà Nội", "Đà Nẵng", "TP.HCM", "Cần Thơ", "Quy Nhơn"],
  "hasEnglishProgram": true,
  "hasInstallmentPolicy": true
}
  `,
  model: google("gemini-2.5-flash-preview-04-17"),
});
