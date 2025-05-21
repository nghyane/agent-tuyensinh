import { MDocument } from '@mastra/rag';

export class VietnameseProcessor {
  private abbreviationPatterns = [
    /TS\./g, /BS\./g, /ThS\./g, /PGS\./g, /GS\./g, /ĐH\./g, 
    /ĐHQG\./g, /THPT\./g, /v\.v\./g
  ];

  /**
   * Phân tách văn bản thành câu cho tiếng Việt, xử lý các trường hợp đặc biệt
   */
  splitIntoSentences(text: string): string[] {
    // Đánh dấu viết tắt để tránh cắt sai
    let markedText = text;
    this.abbreviationPatterns.forEach((pattern, index) => {
      markedText = markedText.replace(pattern, `TS_ABBR_${index}_`);
    });

    // Phân tách câu theo dấu câu tiếng Việt
    const sentencePattern = /(?<!\b\w\.)(?<!\d\.)(?<=[\.\?\!…]|\.\.\.)[\s\n]+(?=[A-ZĐÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ])/g;
    const sentences = markedText.split(sentencePattern).filter(s => s.trim().length > 0);

    // Khôi phục các viết tắt
    return sentences.map(sentence => {
      let restored = sentence;
      this.abbreviationPatterns.forEach((_, index) => {
        restored = restored.replace(new RegExp(`TS_ABBR_${index}_`, 'g'), 
          this.abbreviationPatterns[index].source.replace(/\\./g, '.'));
      });
      return restored.trim();
    });
  }

  /**
   * Phân tách văn bản thành đoạn
   */
  splitIntoParagraphs(text: string): string[] {
    return text.split(/\n{2,}/).filter(p => p.trim().length > 0);
  }

  /**
   * Nhận diện tiêu đề và phân cấp
   */
  extractHeadings(text: string): { level: number, text: string, position: number }[] {
    const headingPattern = /^(#+)\s+(.+)$|^([^\n]+)\n([-=]+)$/gm;
    const headings = [];
    let match;

    while ((match = headingPattern.exec(text)) !== null) {
      if (match[1]) { // Markdown heading (#, ##, etc)
        headings.push({
          level: match[1].length,
          text: match[2].trim(),
          position: match.index
        });
      } else if (match[3] && match[4]) { // Underlined heading (===, ---)
        const level = match[4].startsWith('=') ? 1 : 2;
        headings.push({
          level,
          text: match[3].trim(),
          position: match.index
        });
      }
    }

    return headings;
  }
}
