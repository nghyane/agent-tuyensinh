import { google } from "@ai-sdk/google";
import { embed } from "ai";
import { LibSQLVector } from "@mastra/libsql";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";
import { config } from "dotenv";

// Load environment variables
config();

// Simplified Intent schema
export const IntentSchema = z.object({
  id: z.string(),
  routing: z.enum(['rag', 'database', 'hybrid']),
  tools: z.array(z.string()),
  confidence: z.number().min(0).max(1),
  method: z.enum(['rule', 'vector', 'hybrid'])
});

export type Intent = z.infer<typeof IntentSchema>;

interface IntentExample {
  id: string;
  routing: string;
  tools: string[];
  examples: string[];
}

// Optimized rule pattern with scoring
interface OptimizedRulePattern {
  intentId: string;
  routing: string;
  tools: string[];
  matchers: {
    keywords: string[];
    patterns: RegExp[];
    weight: number;
  };
}

export class HybridIntentDetectionService {
  private vectorDB: LibSQLVector;
  private intentExamples: IntentExample[] = [];
  private rulePatterns: OptimizedRulePattern[] = [];
  private isInitialized = false;
  
  // Optimized thresholds
  private readonly HIGH_CONFIDENCE_THRESHOLD = 0.8; // Use rule-only above this
  private readonly MEDIUM_CONFIDENCE_THRESHOLD = 0.4; // Use vector fallback below this
  private readonly IRRELEVANT_THRESHOLD = 0.1; // Reject below this

  constructor() {
    this.vectorDB = new LibSQLVector({
      connectionUrl: "file:./data/mastra.db",
    });
  }

  /**
   * Optimized initialization
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      await this.loadIntentExamples();
      this.buildOptimizedRulePatterns();
      this.isInitialized = true;
      console.log('⚡ Optimized Intent Detection Service initialized');
    } catch (error) {
      console.error('Failed to initialize service:', error);
      throw error;
    }
  }

  /**
   * Load intent examples (simplified)
   */
  private async loadIntentExamples(): Promise<void> {
    const filePath = path.join(process.cwd(), 'data', 'intent-examples.json');
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const data = JSON.parse(fileContent);
    this.intentExamples = data.intents;
  }

  /**
   * Build optimized rule patterns (consolidated and efficient)
   */
  private buildOptimizedRulePatterns(): void {
    this.rulePatterns = [
      {
        intentId: 'tuition_inquiry',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['học phí', 'tuition', 'phí', 'tiền', 'cost', 'chi phí', 'trả góp', 'thanh toán', 'ojt', 'fee', 'mắc', 'đắt', 'rẻ', 'expensive', 'cheap'],
          patterns: [
            // Tiếng Việt thuần
            /học phí.*(?:bao nhiêu|đắt|rẻ|giá|cost|mắc)/i,
            /(?:chi phí|tiền|phí).*(?:học|ngành|năm|semester|kỳ)/i,
            /(?:đóng|trả|pay|thanh toán).*(?:học phí|tuition|tiền|phí)/i,
            /(?:ojt|thực tập).*(?:đóng|phí|tiền)/i,
            // Mixed English-Vietnamese patterns
            /tuition.*(?:fee|của|bao nhiêu|FPT|program|IT|AI)/i,
            /(?:cost|phí|fee).*(?:của|ngành|program|IT|AI|CNTT)/i,
            /(?:expensive|đắt|mắc|rẻ|cheap).*(?:FPT|tuition|học phí)/i,
            // Specific mixed language patterns with high priority
            /tuition.*fee.*(?:của|program|IT|AI|FPT)/i,
            /(?:fee|phí).*(?:của|of|for).*(?:program|IT|AI)/i,
            // Informal patterns
            /(?:nghe nói|được biết).*(?:FPT|học phí).*(?:đắt|rẻ|mắc|expensive)/i,
            /(?:có thật|thực tế).*(?:không|ko).*(?:đắt|rẻ)/i,
            /(?:flex|worth it).*(?:expensive|đắt)/i,
            // Long detailed queries
            /(?:học phí|tuition).*(?:ngành|program).*(?:bao nhiêu|cost|tiền)/i,
            /(?:4 năm|bốn năm|four years?).*(?:học|cost|phí|tiền)/i,
            // Payment and installment patterns
            /(?:có thể|can).*(?:trả góp|installment|pay monthly)/i,
            /(?:trả góp|installment|monthly payment).*(?:không|possible|available)/i,
            /(?:mỗi tháng|monthly|per month).*(?:bao nhiêu|how much|cost)/i,
            /(?:bao nhiêu|how much).*(?:mỗi tháng|monthly|per month)/i,
            // Context-aware short queries (higher confidence for follow-ups)
            /^(?:mỗi tháng|monthly).*(?:bao nhiêu|how much).*\?*$/i,
            /^(?:có thể|can).*(?:trả góp|installment).*\?*$/i,
            /^(?:bao nhiêu).*(?:tiền|money).*\?*$/i
          ],
          weight: 1.4 // Increased weight for mixed language
        }
      },
      {
        intentId: 'campus_info',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['campus', 'thư viện', 'library', 'lab', 'wifi', 'gym', 'cafeteria', 'ký túc xá', 'gpu', 'rtx', 'cuda', 'facilities'],
        patterns: [
            // Standard patterns
          /thư viện.*(?:mở|đóng|giờ|hoạt động)/i,
            /campus.*(?:hà nội|hcm|đà nẵng|cần thơ|quy nhon|hòa lạc)/i,
            /(?:wifi|mạng).*(?:campus|trường|mạnh|yếu)/i,
            /(?:phòng|lab).*(?:học|thực hành|máy tính)/i,
            // Technical/Mixed language patterns
            /lab.*(?:AI|gpu|rtx|cuda|toolkit|latest version)/i,
            /(?:gpu|rtx|cuda).*(?:để|for|train|model|deep learning)/i,
            /(?:support|hỗ trợ).*(?:cuda|gpu|rtx|latest)/i,
            /(?:facilities|tiện ích|cơ sở).*(?:campus|trường)/i,
            // Campus-specific patterns (avoid tuition conflicts)
            /^(?!.*(?:học phí|phí|tiền|cost|tuition|expensive|đắt|mắc)).*(?:campus|thư viện|lab|wifi).*$/i
          ],
          weight: 1.2
        }
      },
      {
        intentId: 'program_requirements',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['điểm chuẩn', 'điều kiện', 'yêu cầu', 'ielts', 'toefl', 'portfolio', 'xét tuyển', 'requirement', 'khó vào'],
          patterns: [
            /điểm chuẩn.*(?:fpt|năm|bao nhiêu)/i,
            /(?:điều kiện|requirement).*(?:vào|nhập học)/i,
            /(?:ielts|toefl|toeic).*(?:bao nhiêu|yêu cầu|bắt buộc|point)/i,
            /(?:portfolio|hồ sơ).*(?:cần|yêu cầu|nộp)/i,
            // Mixed language patterns
            /(?:ielts|toefl).*requirement.*(?:bao nhiêu|point|điểm)/i,
            /(?:international program).*(?:requirement|yêu cầu)/i,
            // Indirect inquiry patterns
            /(?:nghe nói|được biết).*FPT.*(?:khó vào|điểm chuẩn.*cao)/i,
            /(?:có thật sự|thực tế).*(?:khó|cao|điểm chuẩn)/i
          ],
          weight: 1.25
        }
      },
      {
        intentId: 'program_search',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['ngành', 'major', 'program', 'khóa học', 'curriculum', 'chương trình', 'về', 'muốn hỏi'],
          patterns: [
            /(?:ngành|major).*(?:gì|nào|hot|tốt|dễ)/i,
            /(?:ai|data science|it|cntt).*(?:khác|giống|học)/i,
            /fpt.*(?:có|mở).*ngành/i,
            // Mixed language
            /(?:IT program|AI program|Data Science).*(?:FPT|khác nhau)/i,
            /(?:program|chương trình).*(?:nào|gì|available)/i,
            // General program inquiry patterns
            /(?:muốn hỏi|want to ask).*(?:về|about).*(?:ngành|program|major)/i,
            /(?:về|about).*(?:ngành|program|major).*(?:của|at|ở|in).*FPT/i,
            /(?:ngành|program|major).*AI.*(?:của|at|ở|in).*FPT/i,
            // Career comparison (belongs here, not career_guidance)
            /(?:ai|business|it).*(?:dễ xin việc|job prospects)/i
          ],
          weight: 1.15
        }
      },
      {
        intentId: 'deadline_inquiry',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['hạn', 'deadline', 'khi nào', 'ngày', 'thời gian'],
        patterns: [
            /hạn.*(?:nộp|đăng ký|thi|deadline)/i,
            /(?:deadline|khi nào).*(?:nộp|đăng ký|apply)/i,
            // Mixed language
            /deadline.*(?:đăng ký|registration|semester)/i,
            /(?:registration deadline|hạn đăng ký).*(?:semester|kỳ)/i
        ],
        weight: 1.2
        }
      },
      {
        intentId: 'contact_information',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['hotline', 'số điện thoại', 'email', 'liên hệ', 'contact', 'phone', 'tư vấn', 'counseling', 'hỗ trợ', 'giúp đỡ'],
        patterns: [
          /(?:phòng|văn phòng).*(?:làm việc|mở cửa|giờ)/i,
          /(?:hotline|số|phone).*(?:tư vấn|hỗ trợ)/i,
            // Counseling and support patterns
            /(?:ai|who).*(?:có thể|can).*(?:tư vấn|counsel|help|giúp)/i,
            /(?:tư vấn|counsel|advice).*(?:giúp|help|hỗ trợ)/i,
            /(?:có ai|anyone).*(?:giúp|help|hỗ trợ|tư vấn)/i,
            // Emotional distress patterns (need counseling)
            /(?:stress|áp lực|lo lắng|depressed).*(?:ai|có thể).*(?:tư vấn|giúp)/i,
            /(?:không biết|confused).*(?:ai|who).*(?:tư vấn|help|hỗ trợ)/i,
            // Mental health and psychological support
            /(?:dịch vụ|service).*(?:tâm lý|psychology|mental health).*(?:hỗ trợ|support)/i,
            /(?:tâm lý|psychological|mental).*(?:hỗ trợ|support|counseling)/i,
            /(?:học hành|academic).*(?:áp lực|pressure|stress)/i,
            /(?:áp lực|pressure|stress).*(?:quá|too much|overwhelming)/i,
            // Direct contact requests
            /hotline.*(?:bao nhiêu|number|là gì)/i,
            /(?:số điện thoại|phone number).*(?:tư vấn|support)/i,
            /(?:liên hệ|contact).*(?:ai|who|how)/i
        ],
        weight: 1.1
        }
      },
      {
        intentId: 'scholarship_inquiry',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['học bổng', 'scholarship', 'miễn phí', 'tài trợ', 'giảm học phí', 'hỗ trợ tài chính', 'financial aid'],
        patterns: [
            /học bổng.*(?:100|full|toàn phần|một phần)/i,
            /(?:miễn|giảm).*(?:học phí|100)/i,
            // Direct scholarship patterns
            /(?:có|có thể|available).*học bổng/i,
            /scholarship.*(?:available|có|program)/i,
            /(?:xin|apply).*(?:học bổng|scholarship)/i,
            /(?:điều kiện|requirement).*(?:học bổng|scholarship)/i,
            // Financial need patterns
            /(?:gia đình|family).*(?:không có điều kiện|financial difficulty|poor)/i,
            /(?:miễn phí|free|no cost).*(?:học|study)/i,
            /(?:hỗ trợ|support).*(?:tài chính|financial)/i,
            // Percentage and coverage patterns
            /(?:bao nhiêu|how much).*(?:phần trăm|percent|%)/i,
            /(?:được|cover).*(?:bao nhiêu|how much).*(?:phần trăm|percent)/i,
            // Conditional scholarship patterns
            /(?:nếu|if).*(?:ielts|toefl).*(?:điểm|score|point).*(?:học bổng|scholarship)/i,
            /(?:có thể|can).*(?:xin|apply).*(?:học bổng|scholarship).*(?:ielts|toefl)/i,
            /(?:ielts|toefl).*(?:bao nhiêu|how much).*(?:học bổng|scholarship)/i,
            /(?:học phí|tuition).*(?:giảm|reduce|discount).*(?:bao nhiêu|how much)/i
          ],
          weight: 1.3
        }
      },
      {
        intentId: 'ojt_internship',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['ojt', 'thực tập', 'internship', 'intern'],
        patterns: [
            /ojt.*(?:lương|tiền|bao lâu|điều kiện|nước ngoài)/i,
            /thực tập.*(?:có lương|bao lâu|ở đâu|fail)/i
        ],
          weight: 1.0
        }
      },
      {
        intentId: 'career_guidance',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['việc làm', 'career', 'job', 'tuyển dụng', 'cơ hội', 'tương lai', 'lo lắng', 'chắc chắn'],
        patterns: [
            /(?:98|95).*(?:%|phần trăm).*việc làm/i,
            /việc làm.*(?:có thật|thực tế|đảm bảo)/i,
            // Career anxiety and future concerns
            /(?:học xong|graduate).*(?:có|have).*(?:chắc chắn|sure|guaranteed).*việc làm/i,
            /(?:lo lắng|worry|anxious).*(?:về|about).*(?:tương lai|future|career)/i,
            /(?:có thật|really).*(?:98|95).*(?:%|percent).*(?:việc làm|employment)/i,
            /(?:đảm bảo|guarantee).*(?:việc làm|job|employment)/i,
            // Future prospects
            /(?:tương lai|future).*(?:nghề nghiệp|career|job prospects)/i,
            /(?:cơ hội|opportunity).*(?:nghề nghiệp|career)/i,
            // Employment security concerns
            /(?:chắc chắn|certain|sure).*(?:có|get|find).*(?:việc làm|job)/i,
            /(?:khó|easy|dễ).*(?:xin|find|get).*(?:việc|job)/i
        ],
        weight: 1.0
        }
      },
      {
        intentId: 'special_programs',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['international program', 'chương trình quốc tế', 'dual degree', 'study abroad', 'exchange'],
        patterns: [
            /(?:international|quốc tế).*(?:program|chương trình)/i,
            /(?:dual|kép).*(?:degree|bằng)/i,
            /(?:study abroad|du học|trao đổi)/i,
            /(?:exchange|trao đổi).*(?:program|sinh viên)/i
        ],
        weight: 1.1
        }
      },
      {
        intentId: 'general_info',
        routing: 'rag',
        tools: ['searchKnowledgeBase'],
        matchers: {
          keywords: ['fpt', 'university', 'trường', 'đại học', 'ranking', 'ưu điểm'],
        patterns: [
            /fpt.*(?:thành lập|từ khi|ranking|tầm nhìn)/i,
            /(?:bằng|diploma).*(?:công nhận|valid)/i,
            // Comparison patterns (when not about specific costs)
            /(?:ưu điểm|advantage).*(?:để|why).*(?:đắt hơn|expensive)/i,
            /(?:bách khoa|other university).*(?:so với|vs|compared)/i
        ],
          weight: 0.8
        }
      }
    ];

    console.log(`⚡ Built ${this.rulePatterns.length} optimized patterns`);
  }

  /**
   * Main optimized detection method (rule-first approach)
   */
  async detectIntent(query: string): Promise<Intent> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      // Step 1: Fast rule-based detection first
      const ruleResult = this.detectIntentRule(query);
      
      // Step 2: If high confidence, return immediately (95% of cases)
      if (ruleResult && ruleResult.confidence >= this.HIGH_CONFIDENCE_THRESHOLD) {
        return {
          id: ruleResult.intentId,
          routing: ruleResult.routing as any,
          tools: ruleResult.tools,
          confidence: ruleResult.confidence,
          method: 'rule'
        };
      }

      // Step 3: If very low confidence, check for irrelevant content
      if (!ruleResult || ruleResult.confidence < this.MEDIUM_CONFIDENCE_THRESHOLD) {
        if (this.isIrrelevantContent(query)) {
          return this.createFallbackIntent(0.05); // Very low confidence for irrelevant
        }
      }

      // Step 4: Medium confidence - use vector fallback
      if (ruleResult && ruleResult.confidence >= this.MEDIUM_CONFIDENCE_THRESHOLD) {
        try {
          const vectorResult = await this.detectIntentVector(query);
          
          if (vectorResult) {
            // Hybrid ensemble for medium confidence
            const hybridResult = this.combineResults(ruleResult, vectorResult);
      return {
              id: hybridResult.intentId,
              routing: hybridResult.routing as any,
              tools: hybridResult.tools,
              confidence: hybridResult.confidence,
              method: 'hybrid'
            };
          }
        } catch (error) {
          console.warn('Vector fallback failed, using rule result:', error);
        }
        
        // Fallback to rule result if vector fails
        return {
          id: ruleResult.intentId,
          routing: ruleResult.routing as any,
          tools: ruleResult.tools,
          confidence: ruleResult.confidence,
          method: 'rule'
        };
      }

      // Step 5: Last resort fallback
      return this.createFallbackIntent(0.3);

    } catch (error) {
      console.error('Intent detection failed:', error);
      return this.createFallbackIntent(0.1);
    }
  }

  /**
   * Optimized rule-based detection with multi-intent handling
   */
  private detectIntentRule(query: string): { 
    intentId: string; 
    routing: string; 
    tools: string[]; 
    confidence: number 
  } | null {
    const queryLower = this.normalizeTypos(query.toLowerCase());
    let bestMatch: { intentId: string; routing: string; tools: string[]; score: number } | null = null;
    let allMatches: { intentId: string; routing: string; tools: string[]; score: number; position: number }[] = [];

    for (const pattern of this.rulePatterns) {
      let score = 0;
      let firstMatchPosition = Infinity;

      // Keywords matching
      for (const keyword of pattern.matchers.keywords) {
        const keywordIndex = queryLower.indexOf(keyword.toLowerCase());
        if (keywordIndex !== -1) {
          score += 0.4 * pattern.matchers.weight;
          firstMatchPosition = Math.min(firstMatchPosition, keywordIndex);
        }
      }

      // Pattern matching
      for (const regex of pattern.matchers.patterns) {
        if (regex.test(query) || regex.test(queryLower)) {
          score += 0.6 * pattern.matchers.weight;
          const match = queryLower.match(regex);
          if (match && match.index !== undefined) {
            firstMatchPosition = Math.min(firstMatchPosition, match.index);
          }
        }
      }

      // Apply priority rules for mixed intents
      if (score > 0) {
        score = this.applyPriorityBoost(queryLower, pattern.intentId, score);
        
        allMatches.push({
          intentId: pattern.intentId,
          routing: pattern.routing,
          tools: pattern.tools,
          score: Math.min(score, 1.0),
          position: firstMatchPosition
        });
      }
    }

    // Handle multi-intent queries: prefer intent mentioned first with high enough score
    if (allMatches.length > 1) {
      // Sort by position first, then by score
      allMatches.sort((a, b) => {
        // If position difference is significant (>20 chars), prefer earlier position
        if (Math.abs(a.position - b.position) > 20) {
          return a.position - b.position;
        }
        // Otherwise prefer higher score
        return b.score - a.score;
      });

      // Check if the first match has reasonable score
      const firstMatch = allMatches[0];
      if (firstMatch.score >= 0.6) {
        bestMatch = firstMatch;
      } else {
        // Fall back to highest score if first position match is too weak
        bestMatch = allMatches.sort((a, b) => b.score - a.score)[0];
      }
    } else if (allMatches.length === 1) {
      bestMatch = allMatches[0];
    }

    return bestMatch ? {
      intentId: bestMatch.intentId,
      routing: bestMatch.routing,
      tools: bestMatch.tools,
      confidence: bestMatch.score
    } : null;
  }

  /**
   * Simplified vector detection (only used as fallback)
   */
  private async detectIntentVector(query: string): Promise<{
    intentId: string;
    routing: string;
    tools: string[];
    confidence: number;
  } | null> {
      const { embedding } = await embed({
        value: query,
        model: google.textEmbeddingModel('text-embedding-004'),
      });

      const results = await this.vectorDB.query({
        indexName: "intent_examples",
        queryVector: embedding,
      topK: 3 // Reduced from 5 for performance
      });

      if (results.length === 0) return null;

      const intentAnalysis = this.getBestIntent(results);
    return intentAnalysis;
  }

  /**
   * Enhanced priority boost logic for multi-intent queries
   */
  private applyPriorityBoost(query: string, intentId: string, score: number): number {
    const queryLower = query.toLowerCase();
    
    // Priority 1: Tuition gets highest priority when cost-related keywords present
    if (intentId === 'tuition_inquiry') {
      // Strong tuition indicators
      if (['học phí', 'phí', 'tiền', 'cost', 'tuition', 'expensive', 'đắt', 'rẻ', 'mắc'].some(kw => queryLower.includes(kw))) {
        // Extra boost for mixed English-Vietnamese
        if (queryLower.includes('tuition') && queryLower.includes('fee')) {
          return Math.min(score + 0.4, 1.0); // Very strong boost for "tuition fee"
        }
        // Extra boost for multi-intent queries where tuition is mentioned first
        if (queryLower.match(/^[^.]*?(học phí|tuition|phí|tiền|cost|expensive|đắt)/)) {
          return Math.min(score + 0.3, 1.0); // Strong boost for first mention
        }
        // Boost for indirect tuition inquiries
        if (queryLower.includes('nghe nói') || queryLower.includes('có thật') || queryLower.includes('worth it')) {
          return Math.min(score + 0.25, 1.0);
        }
        return Math.min(score + 0.2, 1.0);
      }
      
      // Context-based tuition detection
      if (queryLower.includes('trả góp') || queryLower.includes('4 năm') || queryLower.includes('bốn năm')) {
        return Math.min(score + 0.2, 1.0);
      }
    }

    // Priority 2: Campus info gets boost for technical/facility questions
    if (intentId === 'campus_info') {
      // Technical facilities boost
      if (['gpu', 'rtx', 'cuda', 'lab', 'wifi', 'thư viện', 'library'].some(kw => queryLower.includes(kw))) {
        // But reduce priority if cost is also mentioned in same query
        if (['học phí', 'phí', 'tiền', 'cost', 'expensive', 'đắt'].some(kw => queryLower.includes(kw))) {
          return Math.max(score - 0.1, 0.1); // Reduce priority when mixed with cost
        }
        return Math.min(score + 0.15, 1.0);
      }
      
      // Location/facilities questions
      if (['campus', 'hà nội', 'hòa lạc', 'cơ sở', 'facilities'].some(kw => queryLower.includes(kw))) {
        // But check if it's not primarily about cost
        if (!queryLower.match(/học phí.*campus|phí.*campus|cost.*campus/)) {
          return Math.min(score + 0.1, 1.0);
        }
      }
    }

    // Priority 3: Requirements get boost for admission-related queries
    if (intentId === 'program_requirements') {
      if (['điểm chuẩn', 'điều kiện', 'ielts', 'yêu cầu', 'requirement', 'khó vào'].some(kw => queryLower.includes(kw))) {
        return Math.min(score + 0.15, 1.0);
      }
      
      // Indirect requirement questions
      if (queryLower.includes('nghe nói') && (queryLower.includes('khó') || queryLower.includes('cao'))) {
        return Math.min(score + 0.1, 1.0);
      }
    }

    // Priority 4: Program search for program comparison questions
    if (intentId === 'program_search') {
      if (['ngành nào', 'program nào', 'khác nhau', 'dễ xin việc'].some(kw => queryLower.includes(kw))) {
        return Math.min(score + 0.1, 1.0);
    }
    }

    // Priority 5: Contact info for emotional/counseling needs
    if (intentId === 'contact_information') {
      if (['stress', 'áp lực', 'ai có thể', 'tư vấn', 'giúp đỡ', 'có ai', 'hotline', 'số điện thoại'].some(kw => queryLower.includes(kw))) {
        return Math.min(score + 0.2, 1.0);
      }
    }

    // Priority 6: Scholarship detection
    if (intentId === 'scholarship_inquiry') {
      // Strong scholarship indicators
      if (['học bổng', 'scholarship', 'miễn phí', 'giảm học phí', 'không có điều kiện', 'phần trăm'].some(kw => queryLower.includes(kw))) {
        return Math.min(score + 0.25, 1.0);
      }
      
      // Financial hardship context
      if (queryLower.includes('gia đình') && (queryLower.includes('không có điều kiện') || queryLower.includes('nghèo'))) {
        return Math.min(score + 0.3, 1.0);
      }
    }

    // Priority 7: Career guidance for anxiety and future concerns
    if (intentId === 'career_guidance') {
      if (['lo lắng', 'worry', 'anxious', 'tương lai', 'chắc chắn', 'guaranteed'].some(kw => queryLower.includes(kw))) {
        return Math.min(score + 0.3, 1.0);
      }
      
      // Employment statistics and claims
      if (queryLower.includes('98%') || queryLower.includes('95%') || queryLower.includes('đảm bảo')) {
        return Math.min(score + 0.2, 1.0);
      }
    }

    // Priority 8: Contact information for stress and mental health
    if (intentId === 'contact_information') {
      // Strong mental health indicators
      if (['áp lực quá', 'stress quá', 'dịch vụ tâm lý', 'hỗ trợ sinh viên'].some(phrase => queryLower.includes(phrase))) {
        return Math.min(score + 0.4, 1.0);
      }
    }

    // Priority 9: Enhanced scholarship detection for conditional queries
    if (intentId === 'scholarship_inquiry') {
      // Conditional scholarship queries
      if ((queryLower.includes('nếu') || queryLower.includes('if')) && 
          (queryLower.includes('ielts') || queryLower.includes('toefl')) && 
          (queryLower.includes('học bổng') || queryLower.includes('scholarship'))) {
        return Math.min(score + 0.35, 1.0);
      }
    }

    // Handle ambiguous queries by reducing confidence for vague contexts
    if (['cái đó', 'cái này', 'nó', 'vậy'].some(vague => queryLower.includes(vague))) {
      // Only apply cost context if there are cost keywords
      if (intentId === 'tuition_inquiry' && !['tiền', 'phí', 'cost', 'expensive', 'đắt'].some(cost => queryLower.includes(cost))) {
        return Math.max(score - 0.2, 0.1);
    }
  }

    // General boost for exact keyword matches
    return score;
  }

  /**
   * Optimized irrelevant content detection
   */
  private isIrrelevantContent(query: string): boolean {
    const queryLower = query.toLowerCase();
    
    const irrelevantKeywords = [
      'thời tiết', 'mưa', 'nắng', 'weather',
      'món ăn', 'phở', 'cơm', 'food', 'ngon',
      'phim', 'nhạc', 'game', 'movie', 'music',
      'bóng đá', 'thể thao', 'sport'
    ];
    
    const hasIrrelevant = irrelevantKeywords.some(kw => queryLower.includes(kw));
    
    // Check for educational context
    const hasEducational = ['fpt', 'university', 'trường', 'học', 'sinh viên', 'ngành'].some(kw => 
      queryLower.includes(kw)
    );
    
    return hasIrrelevant && !hasEducational;
  }

  /**
   * Enhanced typo normalization for Vietnamese and common errors
   */
  private normalizeTypos(query: string): string {
    return query
      // Common Vietnamese typos
      .replace(/hoc/gi, 'học')
      .replace(/phi/gi, 'phí') 
      .replace(/bao nhieu/gi, 'bao nhiêu')
      .replace(/truong/gi, 'trường')
      .replace(/nganh/gi, 'ngành')
      .replace(/cong nghe thong tin/gi, 'công nghệ thông tin')
      
      // Common autocorrect errors  
      .replace(/phi\s+năng\s+khoa/gi, 'phí ngành khoa')
      .replace(/bai\s+nhiều/gi, 'bao nhiêu')
      .replace(/học\s+fi/gi, 'học phí')
      .replace(/tien/gi, 'tiền')
      .replace(/nhieu/gi, 'nhiều')
      
      // Voice-to-text common errors
      .replace(/học\s*fi/gi, 'học phí')
      .replace(/phi\s*học/gi, 'phí học')
      .replace(/hoc\s*fi/gi, 'học phí')
      
      // Mixed language normalizations
      .replace(/tuition\s*phi/gi, 'tuition phí')
      .replace(/it\s*program/gi, 'IT program')
      .replace(/ai\s*program/gi, 'AI program')
      
      // Informal/slang normalizations  
      .replace(/\bmắc\b/gi, 'đắt')
      .replace(/\bko\b/gi, 'không')
      .replace(/\btui\b/gi, 'tôi')
      .replace(/\bđc\b/gi, 'được')
      
      // Remove excessive punctuation
      .replace(/\?{2,}/g, '?')
      .replace(/!{2,}/g, '!')
      .replace(/\.{2,}/g, '.')
      
      // Normalize spacing
      .replace(/\s+/g, ' ')
      .trim();
    }
    
  /**
   * Optimized ensemble logic
   */
  private combineResults(
    ruleResult: { intentId: string; routing: string; tools: string[]; confidence: number },
    vectorResult: { intentId: string; routing: string; tools: string[]; confidence: number }
  ): { intentId: string; routing: string; tools: string[]; confidence: number } {
    
    // Same intent - boost confidence
    if (ruleResult.intentId === vectorResult.intentId) {
      return {
        ...ruleResult,
        confidence: Math.min(ruleResult.confidence * 0.7 + vectorResult.confidence * 0.3 + 0.1, 1.0)
    };
  }

    // Different intents - favor rule (more precise)
    return ruleResult.confidence >= vectorResult.confidence ? ruleResult : vectorResult;
  }

  /**
   * Simplified intent analysis from vector results
   */
  private getBestIntent(results: any[]): {
    intentId: string;
    routing: string;
    tools: string[];
    confidence: number;
  } {
    const intentScores = new Map<string, { score: number; routing: string; tools: string[] }>();
    
    for (const result of results) {
      const intentId = result.metadata?.intentId;
      if (intentId) {
        const existing = intentScores.get(intentId);
        const score = result.score || 0;
        
        if (!existing || score > existing.score) {
          intentScores.set(intentId, {
            score,
            routing: result.metadata?.routing || 'rag',
            tools: result.metadata?.tools || ['searchKnowledgeBase']
          });
        }
      }
    }

    const best = Array.from(intentScores.entries())
      .sort(([,a], [,b]) => b.score - a.score)[0];

    if (best) {
      const [intentId, data] = best;
      return {
        intentId,
        routing: data.routing,
        tools: data.tools,
        confidence: data.score
      };
    }

    return {
      intentId: 'general_info',
      routing: 'rag',
      tools: ['searchKnowledgeBase'],
      confidence: 0.2
    };
  }

  /**
   * Create fallback intent
   */
  private createFallbackIntent(confidence: number): Intent {
    return {
      id: 'general_info',
      routing: 'rag',
      tools: ['searchKnowledgeBase'],
      confidence,
      method: 'rule'
    };
  }

  /**
   * Check if service is ready
   */
  isReady(): boolean {
    return this.isInitialized;
  }
}

// Export singleton instance
export const hybridIntentDetectionService = new HybridIntentDetectionService(); 