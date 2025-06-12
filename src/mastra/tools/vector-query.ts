import { google } from '@ai-sdk/google';
import { createTool } from '@mastra/core/tools';
import { LibSQLVector } from '@mastra/libsql';
import { embed } from 'ai';
import { z } from 'zod';

/**
 * Configuration constants for vector query tool
 */
const CONFIG = {
  /** Default database connection */
  DB_CONNECTION_URL: 'file:./data/mastra.db',
  /** Default index name for university data */
  DEFAULT_INDEX_NAME: 'fpt_university',
  /** Default number of results to return */
  DEFAULT_TOP_K: 5,
  /** Maximum query length for security */
  MAX_QUERY_LENGTH: 1000,
} as const;

/**
 * Default values for fallback scenarios
 */
const DEFAULTS = {
  UNKNOWN_VALUE: 'unknown',
  EMPTY_ARRAY: [] as const,
} as const;

// Type definitions
interface QueryFilters {
  readonly year?: string;
  readonly documentType?: string;
  readonly language?: string;
  readonly campuses?: readonly string[];
  readonly hasEnglishProgram?: boolean;
  readonly hasInstallmentPolicy?: boolean;
  readonly primaryIntents?: readonly string[];
  readonly contentCategories?: readonly string[];
  readonly topicAreas?: readonly string[];
}

interface IntentInfo {
  readonly primaryIntents: readonly string[];
  readonly contentCategories: readonly string[];
  readonly topicAreas: readonly string[];
}

interface DocumentContext {
  readonly source: string;
  readonly type: string;
  readonly year: string;
}

interface EnhancedResult {
  readonly rank: number;
  readonly intentInfo: IntentInfo;
  readonly documentContext: DocumentContext;
  readonly [key: string]: any; // For original result properties
}

interface SearchSummary {
  readonly totalResults: number;
  readonly filtersApplied: readonly string[];
  readonly intentDistribution: Record<string, number>;
  readonly hasIntentFiltering: boolean;
  readonly error?: string;
}

interface VectorSearchResult {
  readonly results: readonly any[];
  readonly searchSummary: {
    readonly totalResults: number;
    readonly filtersApplied: readonly string[];
    readonly intentDistribution: Record<string, number>;
    readonly hasIntentFiltering: boolean;
    readonly error?: string;
  };
}

// Database instance
const dbVector = new LibSQLVector({
  connectionUrl: CONFIG.DB_CONNECTION_URL,
});

// Helper functions
const _buildFilter = (filters: QueryFilters): Record<string, any> => {
  const filter: Record<string, any> = {};

  for (const [key, value] of Object.entries(filters)) {
    if (value && Array.isArray(value) && value.length > 0) {
      // For array filters, use $in operator to match any of the values
      filter[key] = { $in: value };
    } else if (value && !Array.isArray(value)) {
      filter[key] = value;
    }
  }

  return filter;
};

const createIntentInfo = (metadata: any): IntentInfo => ({
  primaryIntents: metadata?.primaryIntents || DEFAULTS.EMPTY_ARRAY,
  contentCategories: metadata?.contentCategories || DEFAULTS.EMPTY_ARRAY,
  topicAreas: metadata?.topicAreas || DEFAULTS.EMPTY_ARRAY,
});

const createDocumentContext = (metadata: any): DocumentContext => ({
  source: metadata?.source || DEFAULTS.UNKNOWN_VALUE,
  type: metadata?.documentType || DEFAULTS.UNKNOWN_VALUE,
  year: metadata?.year || DEFAULTS.UNKNOWN_VALUE,
});

const _enhanceResults = (results: any[]): readonly EnhancedResult[] =>
  results.map((result, index) => ({
    ...result,
    rank: index + 1,
    intentInfo: createIntentInfo(result.metadata),
    documentContext: createDocumentContext(result.metadata),
  }));

const generateIntentDistribution = (results: readonly EnhancedResult[]): Record<string, number> =>
  results.reduce(
    (acc, result) => {
      for (const intent of result.intentInfo.primaryIntents) {
        acc[intent] = (acc[intent] || 0) + 1;
      }
      return acc;
    },
    {} as Record<string, number>
  );

const _createSearchSummary = (
  results: readonly EnhancedResult[],
  appliedFilters: readonly string[],
  error?: string
): SearchSummary => ({
  totalResults: results.length,
  filtersApplied: appliedFilters,
  intentDistribution: error ? {} : generateIntentDistribution(results),
  hasIntentFiltering: !error,
  ...(error && { error }),
});

export const vectorQueryTool = createTool({
  id: 'searchKnowledgeBase',
  description:
    "Search for information in the school's admissions database with intent-aware filtering",
  inputSchema: z.object({
    query: z.string().min(1).max(CONFIG.MAX_QUERY_LENGTH).describe('Search query'),
    topK: z
      .number()
      .int()
      .positive()
      .max(50)
      .optional()
      .describe('Number of results to return (max 50)'),
    filters: z
      .object({
        // Document metadata filters
        year: z.string().optional().describe('Admission year'),
        documentType: z.string().optional().describe('Document type'),
        language: z.string().optional().describe('Language'),
        campuses: z.array(z.string()).optional().describe('Campus areas'),
        hasEnglishProgram: z.boolean().optional().describe('Has English program'),
        hasInstallmentPolicy: z.boolean().optional().describe('Has installment payment policy'),

        // Intent-based filters
        primaryIntents: z.array(z.string()).optional().describe('Filter by specific intents'),
        contentCategories: z.array(z.string()).optional().describe('Filter by content categories'),
        topicAreas: z.array(z.string()).optional().describe('Filter by topic areas'),
      })
      .optional(),
  }),
  execute: async ({ context }): Promise<VectorSearchResult> => {
    const { query, topK = CONFIG.DEFAULT_TOP_K, filters = {} } = context;

    try {
      // Generate embedding
      const { embedding } = await embed({
        value: query,
        model: google.textEmbeddingModel('text-embedding-004'),
      });

      // Build filter object
      const filter: Record<string, any> = {};
      for (const [key, value] of Object.entries(filters)) {
        if (value && Array.isArray(value) && value.length > 0) {
          filter[key] = { $in: value };
        } else if (value && !Array.isArray(value)) {
          filter[key] = value;
        }
      }

      // Execute vector search
      const results = await dbVector.query({
        indexName: CONFIG.DEFAULT_INDEX_NAME,
        queryVector: embedding,
        topK,
        filter: Object.keys(filter).length > 0 ? filter : undefined,
      });

      // Enhanced result processing
      const enhancedResults = results.map((result, index) => {
        const metadata = result.metadata || {};
        return {
          ...result,
          rank: index + 1,
          intentInfo: {
            primaryIntents: metadata.primaryIntents || [],
            contentCategories: metadata.contentCategories || [],
            topicAreas: metadata.topicAreas || [],
          },
          documentContext: {
            source: metadata.source || 'unknown',
            type: metadata.documentType || 'unknown',
            year: metadata.year || 'unknown',
          },
        };
      });

      // Generate intent distribution
      const intentDistribution: Record<string, number> = {};
      for (const result of enhancedResults) {
        for (const intent of result.intentInfo.primaryIntents) {
          intentDistribution[intent] = (intentDistribution[intent] || 0) + 1;
        }
      }

      return {
        results: enhancedResults,
        searchSummary: {
          totalResults: enhancedResults.length,
          filtersApplied: Object.keys(filter),
          intentDistribution,
          hasIntentFiltering: true,
        },
      };
    } catch (_error) {
      console.warn('Vector search failed for query:', `${query.substring(0, 50)}...`);

      return {
        results: [],
        searchSummary: {
          totalResults: 0,
          filtersApplied: [],
          intentDistribution: {},
          hasIntentFiltering: false,
          error: 'Search failed',
        },
      };
    }
  },
});
