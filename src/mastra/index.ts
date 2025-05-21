import { Mastra } from '@mastra/core/mastra';
import { createLogger } from '@mastra/core/logger';
import { LibSQLStore } from '@mastra/libsql';

import { admissionAgent, metadataAgent } from '@/mastra/agents';

export const mastra = new Mastra({
  agents: { admissionAgent, metadataAgent },
  storage: new LibSQLStore({
    url: ":memory:",
  }),
  
  logger: createLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
