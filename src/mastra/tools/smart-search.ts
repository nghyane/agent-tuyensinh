import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { hybridIntentDetectionService } from "@/services/intent-detection-hybrid";

/**
 * Configuration constants for smart search tool - Updated for optimized intent detection
 */
const CONFIG = {
    /** Minimum confidence threshold - lowered to work with optimized detection */
    CONFIDENCE_THRESHOLD: 0.4,
    /** High confidence threshold for reliable results */
    HIGH_CONFIDENCE_THRESHOLD: 0.8,
    /** Very low confidence threshold for questionable results */
    LOW_CONFIDENCE_THRESHOLD: 0.2,
    /** Multiplier to convert confidence to percentage */
    PERCENTAGE_MULTIPLIER: 100,
} as const;

/**
 * Fallback intent when detection fails
 */
const FALLBACK_INTENT = {
    intent: 'general_info',
    confidence: 0.1,
    routing: 'rag',
    tools: ['searchKnowledgeBase'],
    method: 'fallback'
} as const;

// Enhanced type definition with method information
interface SmartSearchResult {
    readonly detectedIntent: {
        readonly intent: string;
        readonly confidence: number;
        readonly routing: string;
        readonly tools: readonly string[];
        readonly method: string;
    };
    readonly query: string;
    readonly smartFiltering: boolean;
    readonly suggestion: string;
    readonly qualityAssessment: {
        readonly isReliable: boolean;
        readonly needsRefinement: boolean;
        readonly confidenceLevel: 'high' | 'medium' | 'low' | 'very_low';
    };
}

export const smartSearchTool = createTool({
    id: "smartSearch",
    description: "Intelligent search with optimized intent detection for Vietnamese and mixed-language queries",
    inputSchema: z.object({
        query: z.string().min(1).describe("User query - supports Vietnamese, English, and mixed language")
    }),
    execute: async ({ context }): Promise<SmartSearchResult> => {
        const { query } = context;
        
        try {
            // Ensure service is initialized before detection
            if (!hybridIntentDetectionService.isReady()) {
                await hybridIntentDetectionService.initialize();
            }
            
            const detectedIntent = await hybridIntentDetectionService.detectIntent(query);
            
            // Enhanced confidence assessment
            const qualityAssessment = assessQuality(detectedIntent.confidence);
            
            // Create context-aware suggestion
            const suggestion = createSuggestion(detectedIntent, qualityAssessment, query);
            
            return {
                detectedIntent: {
                    intent: detectedIntent.id,
                    confidence: detectedIntent.confidence,
                    routing: detectedIntent.routing,
                    tools: detectedIntent.tools,
                    method: detectedIntent.method
                },
                query,
                smartFiltering: detectedIntent.confidence >= CONFIG.CONFIDENCE_THRESHOLD,
                suggestion,
                qualityAssessment
            };

        } catch (error) {
            console.warn('Intent detection failed for query:', query.substring(0, 50) + '...', error);
            
            return {
                detectedIntent: FALLBACK_INTENT,
                query,
                smartFiltering: false,
                suggestion: 'Intent detection unavailable. Using general search without specific filtering.',
                qualityAssessment: {
                    isReliable: false,
                    needsRefinement: true,
                    confidenceLevel: 'very_low'
                }
            };
        }
    }
});

/**
 * Assess the quality of intent detection result
 */
function assessQuality(confidence: number): {
    isReliable: boolean;
    needsRefinement: boolean;
    confidenceLevel: 'high' | 'medium' | 'low' | 'very_low';
} {
    if (confidence >= CONFIG.HIGH_CONFIDENCE_THRESHOLD) {
        return {
            isReliable: true,
            needsRefinement: false,
            confidenceLevel: 'high'
        };
    } else if (confidence >= CONFIG.CONFIDENCE_THRESHOLD) {
        return {
            isReliable: true,
            needsRefinement: false,
            confidenceLevel: 'medium'
        };
    } else if (confidence >= CONFIG.LOW_CONFIDENCE_THRESHOLD) {
        return {
            isReliable: false,
            needsRefinement: true,
            confidenceLevel: 'low'
        };
    } else {
        return {
            isReliable: false,
            needsRefinement: true,
            confidenceLevel: 'very_low'
        };
    }
}

/**
 * Create context-aware suggestion message
 */
function createSuggestion(
    intent: { id: string; confidence: number; method: string },
    quality: { confidenceLevel: string; needsRefinement: boolean },
    query: string
): string {
    const confidencePercent = (intent.confidence * CONFIG.PERCENTAGE_MULTIPLIER).toFixed(1);
    const isMixedLanguage = /[a-zA-Z]/.test(query) && /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(query);
    
    let suggestion = `Detected intent '${intent.id}' with ${confidencePercent}% confidence`;
    
    // Add method information for debugging
    if (intent.method !== 'rule') {
        suggestion += ` (${intent.method} method)`;
    }
    
    // Add quality indicator
    switch (quality.confidenceLevel) {
        case 'high':
            suggestion += '. High confidence - using intent-specific search optimization.';
            break;
        case 'medium':
            suggestion += '. Medium confidence - applying intent-based filtering.';
            break;
        case 'low':
            suggestion += '. Low confidence - consider rephrasing your question for better results.';
            break;
        case 'very_low':
            suggestion += '. Very low confidence - using general search.';
            break;
    }
    
    // Add mixed language tip
    if (isMixedLanguage && quality.confidenceLevel !== 'high') {
        suggestion += ' Try using consistent language (Vietnamese or English) for better detection.';
    }
    
    return suggestion;
} 