import { Mastra } from '@mastra/core/mastra';
import { createLogger } from '@mastra/core/logger';
import { LibSQLStore } from '@mastra/libsql';

import { admissionsAgent, metadataAgent } from '@/mastra/agents';

export const mastra = new Mastra({
  agents: { admissionsAgent, metadataAgent },
  storage: new LibSQLStore({
    url: ":memory:",
  }),
  
  logger: createLogger({
    name: 'Mastra',
    level: 'debug',
  }),
});
