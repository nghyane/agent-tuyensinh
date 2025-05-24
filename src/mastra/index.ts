import { Mastra } from '@mastra/core/mastra';
import { ConsoleLogger } from '@mastra/core/logger';
import { LibSQLStore } from '@mastra/libsql';

import { admissionsAgent, metadataAgent } from '@/mastra/agents';

export const mastra = new Mastra({
  agents: { admissionsAgent, metadataAgent },
  storage: new LibSQLStore({
    url: ":memory:",
  }),
  
  logger: new ConsoleLogger(),
});
